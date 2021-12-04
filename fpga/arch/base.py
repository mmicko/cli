import os
import json
import shutil
import sys
import click
from fpga.util import get_directory
from fpga.util import log, run_command

def getArchitectures():
	arch_dir = os.path.dirname(__file__)
	arch = []
	for cmd_name in os.listdir(arch_dir):
		if cmd_name.startswith("__init__") or cmd_name.startswith("base.py"):
			continue
		if cmd_name.endswith(".py"):
			arch.append(cmd_name[:-3])
	arch.sort()
	return arch

def getArchitectureByName(ctx, name, project):
	mod = None
	try:
		mod = __import__("fpga.arch." + name, None, None, ["create"])
	except(ImportError):
		click.secho('[{}] Invalid architecture {}'.format('validate', name), fg="red")
		sys.exit(-1)
	return mod.create(ctx, project)

def getArchitectureMeta(name):
	with open(os.path.join(get_directory('data'), 'arch', name + '.json')) as json_file:
		data = json.load(json_file)
	return data

def getArchitecturesMeta():
	data = dict()
	for arch in getArchitectures():
		arch_data = getArchitectureMeta(arch)
		for key in arch_data:
			arch_data[key]['arch'] = arch
		data.update(arch_data)
	return data

class BaseArchitecture():
	def __init__(self, ctx, name, project):
		self.name = name
		self.project = project
		self.arch_data = getArchitectureMeta(name)
		self.work_dir = ".fpga"

	def getName(self):
		return self.name

	def getTopParam(self):
		if self.project.getTopModule():
			return "-top {}".format(self.project.getTopModule())
		return ""

	def getFreqParam(self):
		if self.project.getFrequency():
			return '--freq' , str(self.project.getFrequency())
		return []

	def validateProject(self):
		for item in self.arch_data:
			if item['device']==self.project.getDevice():
				if self.project.getPackage() in item['packages']:
					return True
				click.secho('[{}] Unknown package {} for {} device'.format('validate', self.project.getPackage(), self.project.getDevice()), fg="red")
				return False
		click.secho('[{}] Unknown device {} for architecture {}'.format('validate', self.project.getDevice(), self.name), fg="red")
		return False

	def executeYosys(self, scriptfile):
		if (shutil.which('yosys')):
			with open(scriptfile, 'r') as f:
				for line in f.readlines():
					click.secho('[{}] {}'.format('yosys script', line.strip()), fg="yellow")
			params = ['yosys', scriptfile]
			
			#if self.settings.get("verbose") != "True":
			params.append("-q")
			run_command(params, cwd=self.work_dir)#, identifier='yosys')
		else:
			click.secho('Executable for {} not available, install'.format('yosys'), fg="red")

	def executeNextPnR(self, params):
		if (shutil.which('nextpnr-' + self.name)):
			#if self.settings.get("verbose") != "True":
			params.append("-q")
			run_command(['nextpnr-' + self.name] + params, cwd=self.work_dir) #, identifier='nextpnr')
		else:
			click.secho('Executable for {} not available, install'.format('nextpnr-' + self.name), fg="red")
			sys.exit(-1)

	def isUpdateNeeded(self, inputs, output):
		latest = 0
		for x in inputs:
			latest = max(latest,os.stat(x).st_mtime)
		need_update = True
		if (os.path.exists(output)):
			if latest < os.stat(output).st_mtime:
				need_update = False
		return need_update

	def isConstraintGenNeeded(self, output):
		return self.isUpdateNeeded([ self.project.getProjectFilename() ], os.path.join(self.work_dir,output))

	def isSynthNeeded(self, output):
		return self.isUpdateNeeded([ self.project.getProjectFilename() ] + self.project.getSourceFiles(), os.path.join(self.work_dir,output))

	def isPnRNeeded(self, inputFile, output):
		return self.isUpdateNeeded([ os.path.join(self.work_dir,inputFile), os.path.join(self.work_dir,self.getConstraintFile())], os.path.join(self.work_dir,output))

	def executeSynth(self):
		raise NotImplementedError

	def executePnR(self):
		raise NotImplementedError

	def executePack(self):
		raise NotImplementedError

	def executeUpload(self, variant, programmer):
		raise NotImplementedError

	def executeFlash(self, variant, programmer):
		raise NotImplementedError

	def executeBuild(self):
		#click.secho('[{}] Variant {}'.format('build', variant, fg="yellow"))
		self.work_dir = os.path.join(self.work_dir)
		os.makedirs(self.work_dir, exist_ok=True)
		if self.validateProject():
			if self.isConstraintFileGenerated() and self.project.getBoard():
				self.executeGenerateConstrints()
			self.executeSynth()
			self.executePnR()
			self.executePack()

	def removeFileList(self, fileList):
		for file in fileList:
			if (os.path.exists(file)):
				click.secho('[{}] Deleting {}'.format('clean', file, fg="yellow"))
				os.remove(file)

	def executeClean(self, variant):
		click.secho('[{}] Variant {}'.format('clean', variant, fg="yellow"))
		self.work_dir = os.path.join(self.work_dir, variant)
		if os.path.exists(self.work_dir):
			shutil.rmtree(self.work_dir)
		if os.path.exists(".fpga") and not os.listdir(".fpga"):
			os.rmdir(".fpga")

	def isConstraintFileGenerated(self):
		if self.project.getConstraintFiles():
			return False
		return True

	def getConstraintFile(self):
		#if not self.isConstraintFileGenerated():
		return os.path.join("..",self.project.getConstraintFiles()[0])
		#return self.project.getBoard().getConstraintFilename()
		#return ""

	def executeGenerateConstrints(self):
		constraint = self.project.getBoard().getConstraintFilename()
		if self.isConstraintGenNeeded(constraint):
			with open(os.path.join(self.work_dir, constraint), 'w') as f:
				f.write(self.project.getBoard().generateConstraint())
		else:
			click.secho('[{}] No need for generate constraints step'.format('build'))
