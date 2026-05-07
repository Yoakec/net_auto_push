import os
import sys

def _base_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_DIR = os.path.join(_base_dir(), "data")
ARCHIVES_DIR = os.path.join(_base_dir(), "archives")
FRONTEND_DIST = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend", "dist")

SSH_TIMEOUT = 15
DEFAULT_MAX_CONCURRENT = 5
