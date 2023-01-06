import os, sys
if os.name == "posix":
    import resource, fcntl
import subprocess, signal
from select import select
from time import time, localtime
import click


all_tasks_running = []

def force_shutdown(signum, frame):
    click.echo("FPGA ---- Keyboard interrupt or external termination signal ----")
    for task in list(all_tasks_running):
        task.terminate()
    sys.exit(1)

def hook_signals():
    if os.name == "posix":
        signal.signal(signal.SIGHUP, force_shutdown)
    signal.signal(signal.SIGINT, force_shutdown)
    signal.signal(signal.SIGTERM, force_shutdown)

class FPGATask:
    def __init__(self, job, info, deps, cmdline, logfile=None, logstderr=True, silent=False):
        self.running = False
        self.finished = False
        self.terminated = False
        self.checkretcode = False
        self.job = job
        self.info = info
        self.deps = deps
        if os.name == "posix":
            self.cmdline = cmdline
        else:
            # Windows command interpreter equivalents for sequential
            # commands (; => &) command grouping ({} => ()).
            replacements = {
                ";" : "&",
                "{" : "(",
                "}" : ")",
            }

            cmdline_copy = cmdline
            for u, w in replacements.items():
                cmdline_copy = cmdline_copy.replace(u, w)
            self.cmdline = cmdline_copy
        self.logfile = logfile
        self.noprintregex = None
        self.notify = []
        self.linebuffer = ""
        self.logstderr = logstderr
        self.silent = silent

        self.job.tasks_pending.append(self)

        for dep in self.deps:
            dep.register_dep(self)

    def register_dep(self, next_task):
        if self.finished:
            next_task.poll()
        else:
            self.notify.append(next_task)

    def log(self, line):
        if line is not None and (self.noprintregex is None or not self.noprintregex.match(line)):
            if self.logfile is not None:
                click.echo(line, file=self.logfile)
            if line.startswith("Warning:"):
                line = click.style(line, fg="yellow", bold=True)
            elif "ERROR:" in line:
                line = click.style(line, fg="red", bold=True)
            self.job.log(click.style(self.info, fg="magenta") + ": " + line)

    def handle_output(self, line):
        if self.terminated: # or len(line) == 0:
            return
        self.log(line)

    def handle_exit(self, retcode):
        if self.terminated:
            return
        if self.logfile is not None:
            self.logfile.close()
        if (retcode != 0):
            self.job.error("")

    def terminate(self, timeout=False):
        if self.running:
            if not self.silent:
                self.job.log("{}: terminating process".format(click.style(self.info, fg="magenta")))
            if os.name == "posix":
                try:
                    os.killpg(self.p.pid, signal.SIGTERM)
                except PermissionError:
                    pass
            self.p.terminate()
            self.job.tasks_running.remove(self)
            all_tasks_running.remove(self)
        self.terminated = True

    def poll(self):
        if self.finished or self.terminated:
            return

        if not self.running:
            for dep in self.deps:
                if not dep.finished:
                    return

            if not self.silent:
                self.job.log("{}: starting process \"{}\"".format(click.style(self.info, fg="magenta"), self.cmdline))

            if os.name == "posix":
                def preexec_fn():
                    signal.signal(signal.SIGINT, signal.SIG_IGN)
                    os.setpgrp()

                self.p = subprocess.Popen(["/usr/bin/env", "bash", "-c", self.cmdline], stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                        stderr=(subprocess.STDOUT if self.logstderr else None), preexec_fn=preexec_fn)

                fl = fcntl.fcntl(self.p.stdout, fcntl.F_GETFL)
                fcntl.fcntl(self.p.stdout, fcntl.F_SETFL, fl | os.O_NONBLOCK)

            else:
                self.p = subprocess.Popen(self.cmdline, shell=True, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                        stderr=(subprocess.STDOUT if self.logstderr else None))

            self.job.tasks_pending.remove(self)
            self.job.tasks_running.append(self)
            all_tasks_running.append(self)
            self.running = True
            return

        while True:
            outs = self.p.stdout.readline().decode("utf-8")
            if len(outs) == 0: break
            if outs[-1] != '\n':
                self.linebuffer += outs
                break
            outs = (self.linebuffer + outs).rstrip()
            self.linebuffer = ""
            self.handle_output(outs)

        if self.p.poll() is not None:
            if not self.silent:
                self.job.log("{}: finished (returncode={})".format(click.style(self.info, fg="magenta"), self.p.returncode))
            self.job.tasks_running.remove(self)
            all_tasks_running.remove(self)
            self.running = False

            if self.p.returncode == 127:
                self.job.status = "ERROR"
                if not self.silent:
                    self.job.error("{}: COMMAND NOT FOUND. ERROR.".format(click.style(self.info, fg="magenta")))
                self.terminated = True
                self.job.terminate()
                return

            self.handle_exit(self.p.returncode)

            if self.checkretcode and self.p.returncode != 0:
                self.job.status = "ERROR"
                if not self.silent:
                    self.job.error("{}: job failed. ERROR.".format(click.style(self.info, fg="magenta")))
                self.terminated = True
                self.job.terminate()
                return

            self.finished = True
            for next_task in self.notify:
                next_task.poll()
            return


class FPGAAbort(BaseException):
    pass


class FPGAJob:
    def __init__(self, args, cfg, early_logs, configuration, timeout=None):
        self.args = args
        self.cfg = cfg
        self.configuration = configuration
        self.status = "OK"
        self.total_time = 0
        self.timeout = timeout

        self.tasks_running = []
        self.tasks_pending = []

        self.start_clock_time = time()

        if os.name == "posix":
            ru = resource.getrusage(resource.RUSAGE_CHILDREN)
            self.start_process_time = ru.ru_utime + ru.ru_stime

        self.summary = list()

        self.logfile = open("{}/logfile.txt".format(os.path.join(".fpga", self.configuration)), "a")

        for line in early_logs:
            click.echo(line, file=self.logfile)

    def taskloop(self):
        for task in self.tasks_pending:
            task.poll()

        while len(self.tasks_running):
            fds = []
            for task in self.tasks_running:
                if task.running:
                    fds.append(task.p.stdout)

            if os.name == "posix":
                try:
                    select(fds, [], [], 1.0) == ([], [], [])
                except InterruptedError:
                    pass
            else:
                sleep(0.1)

            for task in self.tasks_running:
                task.poll()

            for task in self.tasks_pending:
                task.poll()

            if self.timeout is not None:
                total_clock_time = int(time() - self.start_clock_time)
                if total_clock_time > self.timeout:
                    self.log("Reached TIMEOUT ({} seconds). Terminating all tasks.".format(self.timeout))
                    self.status = "TIMEOUT"
                    self.terminate(timeout=True)

    def dress_message(self, logmessage):
        tm = localtime()
        return " ".join([
            click.style("FPGA", fg="blue"),
            click.style("{:2d}:{:02d}:{:02d}".format(tm.tm_hour, tm.tm_min, tm.tm_sec), fg="green"),
            "[" + click.style(self.configuration, fg="blue") + "]",
            logmessage
        ])

    def log(self, logmessage):
        text = self.dress_message(logmessage)
        click.echo(text)
        click.echo(text, file=self.logfile)

    def warning(self, logmessage):
        text = self.dress_message(click.style("Warning: " + logmessage, fg="yellow", bold=True))
        click.echo(text)
        click.echo(text, file=self.logfile)

    def error(self, logmessage):
        if (logmessage):
            text = self.dress_message(click.style("ERROR: " + logmessage, fg="red", bold=True))
            click.echo(text)
            click.echo(text, file=self.logfile)
        self.status = "ERROR"
        self.retcode = 16
        self.terminate()
        with open("{}/{}".format(os.path.join(".fpga", self.configuration), self.status), "w") as f:
            click.echo(logmessage, file=f)
        raise FPGAAbort(logmessage)

    def terminate(self, timeout=False):
        for task in list(self.tasks_running):
            task.terminate(timeout=timeout)

    def run(self):
        self.taskloop()

    def final(self):
        total_clock_time = int(time() - self.start_clock_time)

        if os.name == "posix":
            ru = resource.getrusage(resource.RUSAGE_CHILDREN)
            total_process_time = int((ru.ru_utime + ru.ru_stime) - self.start_process_time)
            self.total_time = total_process_time

            self.summary = [
                "Elapsed clock time [H:MM:SS (secs)]: {}:{:02d}:{:02d} ({})".format
                        (total_clock_time // (60*60), (total_clock_time // 60) % 60, total_clock_time % 60, total_clock_time),
                "Elapsed process time [H:MM:SS (secs)]: {}:{:02d}:{:02d} ({})".format
                        (total_process_time // (60*60), (total_process_time // 60) % 60, total_process_time % 60, total_process_time),
            ] + self.summary
        else:
            self.summary = [
                "Elapsed clock time [H:MM:SS (secs)]: {}:{:02d}:{:02d} ({})".format
                        (total_clock_time // (60*60), (total_clock_time // 60) % 60, total_clock_time % 60, total_clock_time),
                "Elapsed process time unvailable on Windows"
            ] + self.summary

        for line in self.summary:
            self.log(click.style("summary", fg="magenta") + ": " + line)

        self.retcode = 0
        if self.status == "TIMEOUT": self.retcode = 8
        if self.status == "ERROR": self.retcode = 16

        self.log("DONE ({}, rc={})".format(self.status, self.retcode))
