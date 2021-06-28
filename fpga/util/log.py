import click

class log:
	@staticmethod
	def warning(msg):
		click.secho("==> WARNING : ", fg="yellow", nl=False, bold=True)
		click.secho(msg, fg="white", bold=True)

	@staticmethod
	def error(msg):
		click.secho("\n==> ERROR : ", fg="red", nl=False, bold=True)
		click.secho(msg, fg="white", bold=True)
		sys.exit(-1)

	@staticmethod
	def info(msg):
		click.secho("==> ", fg="green", nl=False, bold=True)
		click.secho(msg, fg="white", bold=True)

	@staticmethod
	def step(msg):
		click.secho("  -> ", fg="blue", nl=False, bold=True)
		click.secho(msg, fg="white", bold=True)

