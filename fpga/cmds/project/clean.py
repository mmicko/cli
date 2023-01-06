import click
from fpga.util.project import Project

@click.command('clean', help='Clean FPGA project')
@click.pass_context
def cli(ctx):
    proj = Project("apio.ini", ctx)
    arch = proj.getArchitecture()
    arch.executeClean()
