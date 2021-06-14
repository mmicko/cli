import click

@click.command('boards', help='Manage FPGA boards.')
@click.pass_context
def cli(ctx):
    pass