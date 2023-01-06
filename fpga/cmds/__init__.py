import os
import click

class FPGACLI(click.MultiCommand):

    def __init__(self, *args, **kwargs):
        super(FPGACLI, self).__init__(*args, **kwargs)
        self._cmds_dir = os.path.dirname(__file__)
        self._groups = []
        self._cmd_map = dict()
        self._group_map = dict()
        self._group_map["project"] = "Project commands:"
        self._group_map["setup"] = "Setup commands:"
        self._group_map["util"] = "Utility commands:"
        for group in os.listdir(self._cmds_dir):
            if group.startswith("__pycache__"):
                continue
            path = os.path.join(self._cmds_dir, group)
            if os.path.isdir(path):
                self._groups.append(group)
        self._groups.sort()
        self.list_commands(None)

    def list_commands(self, ctx):
        cmds = []
        for group_name in self._groups:
            path = os.path.join(self._cmds_dir, group_name)
            for cmd_name in os.listdir(path):
                if cmd_name.startswith("__init__"):
                    continue
                if cmd_name.endswith(".py"):
                    cmds.append(cmd_name[:-3])
                    self._cmd_map[cmd_name[:-3]] = group_name
        cmds.sort()
        return cmds

    def get_command(self, ctx, cmd_name):
        mod = None
        try:
            mod = __import__("fpga.cmds." + self._cmd_map[cmd_name] + "." + cmd_name, None, None, ["cli"])
        except:
            raise click.UsageError('No such command "%s"' % cmd_name, ctx)
        return mod.cli

    def get_help(self, ctx):
        formatter = ctx.make_formatter()
        self.format_usage(ctx, formatter)
        self.format_help_text(ctx, formatter)
        click.Command.format_options(self, ctx, formatter)
        cmd_formatter = ctx.make_formatter()
        self.format_commands(ctx, cmd_formatter)
        help_lines = cmd_formatter.getvalue().rstrip("\n").split("\n")[1:]
        for group_name in self._groups:
            formatter.write_paragraph()
            formatter.write_text(self._group_map[group_name])
            for line in help_lines:
                if (self._cmd_map[line.strip().split()[0]] == group_name):
                    formatter.write_text(line)

        self.format_epilog(ctx, formatter)
        return formatter.getvalue()
