# Designer imports this file as a top-level module, so find the package it is
# part of from its location.

import importlib
import pathlib

package = pathlib.Path(__file__).resolve().parents[2].name
importlib.import_module(package + '.tests.exceptiondialog').install()
