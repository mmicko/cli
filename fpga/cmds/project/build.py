import click
from fpga.util.project import Project

@click.command('build', help='Build FPGA project')
@click.pass_context
def cli(ctx):
    proj = Project("apio.ini", ctx)
    arch = proj.getArchitecture()
    arch.executeBuild()
