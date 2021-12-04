import glob
from fpga.arch import getArchitectureByName

class Project():
	def __init__(self, filename, ctx):
		self.ctx = ctx
		self.filename = filename

	def getProjectFilename(self):
		return self.filename

	def getArchitecture(self):
		return getArchitectureByName(self.ctx, "ice40", self)

	def getDevice(self):
		return "up5k"

	def getTopModule(self):
		return None

	def getFrequency(self):
		return None

	def getPackage(self):
		return "sg48"

	def getConstraintFiles(self):
		return [f for f in glob.glob("*.pcf")]

	def getBoard(self):
		return None

	def getSourceFiles(self):		
		return [f for f in glob.glob("*.v")]