import click
from fpga.util.project import Project
#from fpga.util import log, run_command

@click.command('build', help='Build FPGA project')
@click.pass_context
def cli(ctx):
	proj = Project("apio.ini", ctx)
	arch = proj.getArchitecture()
	arch.executeBuild()
