import os
import sys
import shutil
import tempfile
import click
from fpga.arch.base import BaseArchitecture
from fpga.util import log, run_command

class ICE40Architecture(BaseArchitecture):
	def __init__(self, ctx, project):
		super().__init__(ctx, "ice40", project)

	def executeSynth(self):
		if self.isSynthNeeded('output.json'):
			with tempfile.NamedTemporaryFile(mode='w+', suffix='.ys') as fp:
				for x in self.project.getSourceFiles():
					fp.write('read_verilog ' + os.path.join("..",x) + '\n')
				fp.write('synth_ice40 {}\n'.format(self.getTopParam()))
				fp.write('write_json output.json\n')
				fp.seek(0)
				self.executeYosys(fp.name)
		else:
			click.secho('[{}] No need for synthesis step'.format('build'))

	def executePnR(self):
		if self.isPnRNeeded('output.json', 'output.asc'):
			params = [
				'--'+self.project.getDevice(),
				'--package', self.project.getPackage(),
				'--pcf', self.getConstraintFile(),
				'--json', 'output.json',
				'--asc', 'output.asc'
			]
			params.extend(self.getFreqParam())
			self.executeNextPnR(params)
		else:
			click.secho('[{}] No need for place and route step'.format('build'))

	def executePack(self):
		if self.isUpdateNeeded([os.path.join(self.work_dir,'output.asc')],os.path.join(self.work_dir,'output.bin')):
			if (shutil.which('icepack')):
				run_command(['icepack', 'output.asc', 'output.bin'], cwd=self.work_dir) #, identifier='icepack')
			else:
				click.secho('Executable for {} not available, install'.format('icepack'), fg="red")
				sys.exit(-1)
		else:
			click.secho('[{}] No need for packing step'.format('build'))

#	def executeUpload(self, variant, programmer):
#		self.executeBuild(variant)
#		programmer.loadBitstream(os.path.join(self.work_dir,'output.bin'))
#
#	def executeFlash(self, variant, programmer):
#		self.executeBuild(variant)
#		programmer.loadFlash(os.path.join(self.work_dir,'output.bin'))

def create(ctx, project):
	return ICE40Architecture(ctx, project)
