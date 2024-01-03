""" Enables support for calling entrypoints using `python -m` or `pythonw -m`.
On windows using `pythonw -m pyqt6_tools designer` in a shortcut allows opening
QtDesigner without showing a command prompt window that stays open the entire
time that QtDesigner is open.
"""


import importlib
import pathlib
import sys

if __name__ == "__main__":
    # Relative imports don't work when called by `python -m ...`, get the name
    # of the parent folder so we can import entrypoints from it. This is needed
    # because the package name is not hard coded between PyQt versions.
    module_name = pathlib.Path(__file__).parent.stem
    entrypoints = importlib.import_module(f"{module_name}.entrypoints")

    sys.exit(entrypoints.main())
