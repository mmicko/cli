import click, signal, os, sys
from fpga.cmds import FPGACLI
from fpga.__init__ import __version__

def force_shutdown(signum, frame):
	if (os.name != 'nt' and signum != signal.SIGPIPE):
		click.secho("\n==> Keyboard interrupt or external termination signal", fg="red", nl=True, bold=True)
	sys.exit(1)

@click.group(cls=FPGACLI, help="""FPGA - Command Line Interface\n""", invoke_without_command=True)
@click.version_option(__version__)
@click.pass_context
def cli(ctx):
	if os.name == "posix":
		signal.signal(signal.SIGHUP, force_shutdown)
		signal.signal(signal.SIGPIPE, force_shutdown)
	signal.signal(signal.SIGINT, force_shutdown)
	signal.signal(signal.SIGTERM, force_shutdown)

	ctx.ensure_object(dict)
	if ctx.invoked_subcommand is None:
		click.secho(ctx.get_help())
	pass
