import importlib
import pathlib

# Designer imports this file as a top-level module, so find the package it is
# part of from its location.
pyqt_plugins = importlib.import_module(pathlib.Path(__file__).resolve().parent.parent.name)
import_it = pyqt_plugins.import_it
major = pyqt_plugins.major

QtDesigner = import_it("PyQt", "QtDesigner")


class RedPlugin(QtDesigner.QPyDesignerCustomWidgetPlugin):
    # https://wiki.python.org/moin/PyQt/Using_Python_Custom_Widgets_in_Qt_Designer

    def __init__(self):
        raise Exception('This exception is being intentionally raised to demonstrate the pyqt{}-tools exception dialog.'.format(major))
