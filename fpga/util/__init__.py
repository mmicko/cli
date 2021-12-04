import os

from .log import log
from .run import run_command

def get_directory(name):
	return os.path.join(os.path.dirname(__file__), '..', name)
