import os
import json
import shutil
import sys
import click
from fpga.util import get_directory
from fpga.util import FPGAJob, FPGATask, FPGAAbort

def getArchitectures():
    arch_dir = os.path.dirname(__file__)
    arch = []
    for cmd_name in os.listdir(arch_dir):
        if cmd_name.startswith("__init__") or cmd_name.startswith("base.py"):
            continue
        if cmd_name.endswith(".py"):
            arch.append(cmd_name[:-3])
    arch.sort()
    return arch

def getArchitectureByName(ctx, name, project):
    mod = None
    try:
        mod = __import__("fpga.arch." + name, None, None, ["create"])
    except(ImportError):
        click.secho('[{}] Invalid architecture {}'.format('validate', name), fg="red")
        sys.exit(-1)
    return mod.create(ctx, project)

def getArchitectureMeta(name):
    with open(os.path.join(get_directory('data'), 'arch', name + '.json')) as json_file:
        data = json.load(json_file)
    return data

def getArchitecturesMeta():
    data = dict()
    for arch in getArchitectures():
        arch_data = getArchitectureMeta(arch)
        for key in arch_data:
            arch_data[key]['arch'] = arch
        data.update(arch_data)
    return data

class BaseArchitecture():
    def __init__(self, ctx, name, project):
        self.name = name
        self.project = project
        self.arch_data = getArchitectureMeta(name)
        self.work_dir = os.path.join(".fpga", project.getConfiguration())
        os.makedirs(self.work_dir, exist_ok=True)
        self.job = FPGAJob([], [], [], project.getConfiguration())

    def getName(self):
        return self.name

    def getTopParam(self):
        if self.project.getTopModule():
            return "-top {}".format(self.project.getTopModule())
        return ""

    def getFreqParam(self):
        if self.project.getFrequency():
            return '--freq' , str(self.project.getFrequency())
        return []

    def validateProject(self):
        for item in self.arch_data:
            if item['device']==self.project.getDevice():
                if self.project.getPackage() in item['packages']:
                    return True
                click.secho('[{}] Unknown package {} for {} device'.format('validate', self.project.getPackage(), self.project.getDevice()), fg="red")
                return False
        click.secho('[{}] Unknown device {} for architecture {}'.format('validate', self.project.getDevice(), self.name), fg="red")
        return False

    def executeYosys(self, scriptfile):
        if (shutil.which('yosys')):
            #with open(scriptfile, 'r') as f:
            #	for line in f.readlines():
            #		click.secho('[{}] {}'.format('yosys script', line.strip()), fg="yellow")
            #if self.settings.get("verbose") != "True":
            #params.append("-q")
            #run_command(params, cwd=self.work_dir)#, identifier='yosys')
            FPGATask(self.job, "synth", [], f"yosys {scriptfile} -q")
            self.job.run()
        
        else:
            click.secho('Executable for {} not available, install'.format('yosys'), fg="red")

    def executeNextPnR(self, params):
        if (shutil.which('nextpnr-' + self.name)):
            #if self.settings.get("verbose") != "True":
            #params.append("-q")
            #run_command(['nextpnr-' + self.name] + params, cwd=self.work_dir) #, identifier='nextpnr')
            FPGATask(self.job, "pnr", [], f"nextpnr-{self.name} " + " ".join(params) + " -q")
            self.job.run()
        else:
            click.secho('Executable for {} not available, install'.format('nextpnr-' + self.name), fg="red")
            sys.exit(-1)

    def isUpdateNeeded(self, inputs, output):
        latest = 0
        for x in inputs:
            latest = max(latest,os.stat(x).st_mtime)
        need_update = True
        if (os.path.exists(output)):
            if latest < os.stat(output).st_mtime:
                need_update = False
        return need_update

    def isConstraintGenNeeded(self, output):
        return self.isUpdateNeeded([ self.project.getProjectFilename() ], os.path.join(self.work_dir,output))

    def isSynthNeeded(self, output):
        return self.isUpdateNeeded([ self.project.getProjectFilename() ] + self.project.getSourceFiles(), os.path.join(self.work_dir,output))

    def isPnRNeeded(self, inputFile, output):
        return self.isUpdateNeeded([ inputFile, self.getConstraintFile()], os.path.join(self.work_dir,output))

    def executeSynth(self):
        raise NotImplementedError

    def executePnR(self):
        raise NotImplementedError

    def executePack(self):
        raise NotImplementedError

    def executeUpload(self, variant, programmer):
        raise NotImplementedError

    def executeFlash(self, variant, programmer):
        raise NotImplementedError

    def executeBuild(self):
        os.makedirs(self.work_dir, exist_ok=True)
        if self.validateProject():
            try:
                self.executeSynth()
                self.executePnR()
                self.executePack()
            except FPGAAbort:
                pass
            self.job.final()

    def executeClean(self):
        self.job.log(click.style("clean", fg="magenta") + ": Cleaning")
        if os.path.exists(self.work_dir):
            shutil.rmtree(self.work_dir)
        self.job.final()

    def getConstraintFile(self):
        return self.project.getConstraintFiles()[0]
