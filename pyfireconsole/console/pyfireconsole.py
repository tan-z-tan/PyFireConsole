import glob
import importlib.util
import inspect
import os
import sys
from typing import Optional

from IPython.terminal.embed import embed


class PyFireConsole:
    def __init__(self, model_dir: Optional[str] = None):
        self.model_dir = model_dir

    def run(self, reset_global=False):
        # Get the caller's global namespace
        caller_globals = inspect.currentframe().f_back.f_globals

        # If a model directory is specified, add it to the system path
        if self.model_dir:
            module_path = os.path.abspath(self.model_dir)
            if module_path not in sys.path:
                sys.path.append(module_path)

            # Import all the python files as modules
            for filename in glob.glob(os.path.join(module_path, '*.py')):
                module_name = os.path.splitext(os.path.basename(filename))[0]
                spec = importlib.util.spec_from_file_location(module_name, filename)
                module = importlib.util.module_from_spec(spec)

                spec.loader.exec_module(module)

                # Inspect all classes in the module and add them to global namespace
                for _, obj in inspect.getmembers(module):
                    # Import iff the object is a class and is not already in the global namespace
                    if inspect.isclass(obj) and obj.__module__ == module_name and obj.__name__ not in caller_globals:
                        print(f"Importing {obj.__name__} from {module_name}")
                        caller_globals[obj.__name__] = obj

        # Start the interactive shell
        user_ns = None if reset_global else caller_globals
        embed(banner1="\n==================== Welcome to PyFireConsole ====================\n", exit_msg="Bye", user_ns=user_ns, confirm_exit=False)
