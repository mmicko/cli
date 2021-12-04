import os
import sys
import shutil
import tempfile
import click
from fpga.arch.base import BaseArchitecture
from fpga.util.commands import run_command

class ECP5Architecture(BaseArchitecture):
	def __init__(self, ctx, project):
		super().__init__(ctx, "ecp5", project)

	def executeSynth(self):
		if self.isSynthNeeded('output.json'):
			with tempfile.NamedTemporaryFile(mode='w+', suffix='.ys') as fp:
				for x in self.project.getSourceFiles():
					fp.write('read_verilog ' + os.path.join("..","..",x) + '\n')
				fp.write('synth_ecp5 {}\n'.format(self.getTopParam()))
				fp.write('write_json output.json\n')
				fp.seek(0)
				self.executeYosys(fp.name)
		else:
			click.secho('[{}] No need for synthesis step'.format('build'))

	def executePnR(self):
		if self.isPnRNeeded('output.json', 'output.config'):
			params = [
				'--'+self.project.getDevice(),
				'--package', self.project.getPackage(),
				'--lpf', self.getConstraintFile(),
				'--json', 'output.json',
				'--textcfg', 'output.config'
			]
			params.extend(self.getFreqParam())
			self.executeNextPnR(params)
		else:
			click.secho('[{}] No need for place and route step'.format('build'))

	def executePack(self):
		if self.isUpdateNeeded([os.path.join(self.work_dir,'output.config')],os.path.join(self.work_dir,'output.bin')):
			if (shutil.which('ecppack')):
				run_command(['ecppack', 'output.config', 'output.bin'], cwd=self.work_dir, identifier='ecppack')
			else:
				click.secho('Executable for {} not available, install'.format('ecppack'), fg="red")
				sys.exit(-1)
		else:
			click.secho('[{}] No need for packing step'.format('build'))

	def executeUpload(self, variant, programmer):
		self.executeBuild(variant)
		programmer.loadBitstream(os.path.join(self.work_dir,'output.bin'))

	def executeFlash(self, variant, programmer):
		self.executeBuild(variant)
		programmer.loadFlash(os.path.join(self.work_dir,'output.bin'))

def create(ctx, project):
	return ECP5Architecture(ctx, project)
