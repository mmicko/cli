import click
from fpga.cmds import FPGACLI
from fpga.util import hook_signals
from fpga.__init__ import __version__

@click.group(cls=FPGACLI, help="""FPGA - Command Line Interface\n""", invoke_without_command=True)
@click.version_option(__version__)
@click.pass_context
def cli(ctx):
    hook_signals()
    ctx.ensure_object(dict)
    if ctx.invoked_subcommand is None:
        click.secho(ctx.get_help())
    pass
