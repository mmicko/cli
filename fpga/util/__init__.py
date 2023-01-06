import os

from .log import log
from .job import hook_signals, FPGAJob, FPGATask, FPGAAbort

def get_directory(name):
    return os.path.join(os.path.dirname(__file__), '..', name)
