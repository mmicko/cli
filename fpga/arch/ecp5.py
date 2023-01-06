import os
import sys
import shutil
import click
from fpga.arch.base import BaseArchitecture
from fpga.util import FPGATask

class ECP5Architecture(BaseArchitecture):
    def __init__(self, ctx, project):
        super().__init__(ctx, "ecp5", project)

    def executeSynth(self):
        if self.isSynthNeeded('output.json'):
            with open(os.path.join(self.work_dir,'script.ys'), "w") as f:
                for x in self.project.getSourceFiles():
                    print(f"read_verilog {x}", file=f)
                print(f"synth_ecp5 {self.getTopParam()}", file=f)
                print(f"write_json {os.path.join(self.work_dir, 'output.json')}", file=f)
            self.executeYosys(os.path.join(self.work_dir,'script.ys'))
        else:
            self.job.log('No need for synthesis step')

    def executePnR(self):
        if self.isPnRNeeded(os.path.join(self.work_dir,'output.json'), 'output.config'):
            params = [
                '--'+self.project.getDevice(),
                '--package', self.project.getPackage(),
                '--lpf', self.getConstraintFile(),
                '--json', os.path.join(self.work_dir, 'output.json'),
                '--textcfg', os.path.join(self.work_dir, 'output.config')
            ]
            params.extend(self.getFreqParam())
            self.executeNextPnR(params)
        else:
            self.job.log('No need for place and route step')

    def executePack(self):
        if self.isUpdateNeeded([os.path.join(self.work_dir,'output.config')],os.path.join(self.work_dir,'output.bin')):
            if (shutil.which('ecppack')):
                FPGATask(self.job, "pack", [], f"ecppack {os.path.join(self.work_dir, 'output.config')} {os.path.join(self.work_dir, 'output.bin')}")
            else:
                click.secho('Executable for {} not available, install'.format('ecppack'), fg="red")
                sys.exit(-1)
        else:
            self.job.log('No need for packing step')

    def executeUpload(self, variant, programmer):
        self.executeBuild(variant)
        programmer.loadBitstream(os.path.join(self.work_dir,'output.bin'))

    def executeFlash(self, variant, programmer):
        self.executeBuild(variant)
        programmer.loadFlash(os.path.join(self.work_dir,'output.bin'))

def create(ctx, project):
    return ECP5Architecture(ctx, project)
