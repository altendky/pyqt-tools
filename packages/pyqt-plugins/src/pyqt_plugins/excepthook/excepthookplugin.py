# Put this directory first in PYQTDESIGNERPATH so that Designer imports this
# before any other Python plugin and their exceptions are shown in a dialog.
#
# Designer imports this file as a top-level module, so find the package it is
# part of from its location.

import importlib
import pathlib

package = pathlib.Path(__file__).resolve().parent.parent.name
importlib.import_module(package + '.exceptiondialog').install()
