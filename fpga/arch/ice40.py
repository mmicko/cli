import os
import sys
import shutil
import click
from fpga.arch.base import BaseArchitecture
from fpga.util import FPGATask

class ICE40Architecture(BaseArchitecture):
    def __init__(self, ctx, project):
        super().__init__(ctx, "ice40", project)

    def executeSynth(self):
        if self.isSynthNeeded('output.json'):
            with open(os.path.join(self.work_dir,'script.ys'), "w") as f:
                for x in self.project.getSourceFiles():
                    print(f"read_verilog {x}", file=f)
                print(f"synth_ice40 {self.getTopParam()}", file=f)
                print(f"write_json {os.path.join(self.work_dir, 'output.json')}", file=f)
            self.executeYosys(os.path.join(self.work_dir,'script.ys'))
        else:
            self.job.log(click.style("synth", fg="magenta") + ": No need for synthesis step")

    def executePnR(self):
        if self.isPnRNeeded(os.path.join(self.work_dir,'output.json'), 'output.asc'):
            params = [
                '--'+self.project.getDevice(),
                '--package', self.project.getPackage(),
                '--pcf', self.getConstraintFile(),
                '--json', os.path.join(self.work_dir, 'output.json'),
                '--asc', os.path.join(self.work_dir, 'output.asc')
            ]
            params.extend(self.getFreqParam())
            self.executeNextPnR(params)
        else:
            self.job.log(click.style("pnr", fg="magenta") + ": No need for place and route step")

    def executePack(self):
        if self.isUpdateNeeded([os.path.join(self.work_dir,'output.asc')],os.path.join(self.work_dir,'output.bin')):
            if shutil.which('icepack'):
                FPGATask(self.job, "pack", [], f"icepack {os.path.join(self.work_dir, 'output.asc')} {os.path.join(self.work_dir, 'output.bin')}")
                self.job.run()
            else:
                click.secho('Executable for {} not available, install'.format('icepack'), fg="red")
                sys.exit(-1)
        else:
            self.job.log(click.style("pack", fg="magenta") + ": No need for packing step")

#	def executeUpload(self, variant, programmer):
#		self.executeBuild(variant)
#		programmer.loadBitstream(os.path.join(self.work_dir,'output.bin'))
#
#	def executeFlash(self, variant, programmer):
#		self.executeBuild(variant)
#		programmer.loadFlash(os.path.join(self.work_dir,'output.bin'))

def create(ctx, project):
    return ICE40Architecture(ctx, project)
