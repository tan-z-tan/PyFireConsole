from typing import Optional
from IPython.terminal.embed import embed
import os
import sys
import glob
import importlib
import inspect


class PyFireConsole:
    def __init__(self, model_dir: Optional[str] = None):
        self.model_dir = model_dir

    def run(self, reset_global=False):
        # If a model directory is specified, add it to the system path
        if self.model_dir:
            module_path = os.path.abspath(self.model_dir)
            if module_path not in sys.path:
                sys.path.append(module_path)

            # Import all the python files as modules
            for filename in glob.glob(os.path.join(module_path, '*.py')):
                importlib.import_module(os.path.basename(filename)[:-3])

        # Start the interactive shell
        user_ns = None if reset_global else inspect.currentframe().f_back.f_globals
        embed(banner1="\nWelcome to PyFireConsole ====================\n", exit_msg="Bye", user_ns=user_ns, confirm_exit=False)
