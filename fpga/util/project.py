import glob
import configparser
import json
import os
from fpga.util import get_directory
from fpga.arch import getArchitectureByName

class Project():
    def __init__(self, filename, ctx):
        self.ctx = ctx
        self.filename = filename
        config = configparser.ConfigParser()
        config.read(filename)

        with open(os.path.join(get_directory('data'), 'apio', 'boards.json')) as json_file:
            boards = json.load(json_file)
        with open(os.path.join(get_directory('data'), 'apio', 'fpgas.json')) as json_file:
            fpgas = json.load(json_file)
        self.board = config.get("env", "board")
        f = fpgas[boards[self.board]["fpga"]]
        self.arch = f["arch"]
        if self.arch=="ice40":
            self.device = f["type"]+f["size"]
        else:
            self.device = f["type"]
        self.package = f["pack"]

    def getProjectFilename(self):
        return self.filename

    def getArchitecture(self):
        return getArchitectureByName(self.ctx, self.arch, self)

    def getDevice(self):
        return self.device

    def getTopModule(self):
        return None

    def getFrequency(self):
        return None

    def getPackage(self):
        return self.package

    def getConstraintFiles(self):
        if self.arch=="ice40":
            return [f for f in glob.glob("*.pcf")]
        if self.arch=="ecp5":
            return [f for f in glob.glob("*.lpf")]

    def getBoard(self):
        return None

    def getSourceFiles(self):
        files = set(glob.glob("*.v")) - set(glob.glob("*_tb.v"))
        return [f for f in files]

    def getConfiguration(self):
        return self.board
