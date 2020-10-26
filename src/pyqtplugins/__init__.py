import os
import pathlib

import PyQt5


root = pathlib.Path(__file__).resolve().parent
# TODO: so apparently qml wants it all lower case...
if sys.platform == 'win32':
    root = pathlib.Path(os.fspath(root).lower())
plugins = root.joinpath('Qt', 'plugins')

pyqt5_root = pathlib.Path(PyQt5.__file__).resolve().parent
pyqt5_qml_path = pyqt5_root.joinpath('Qt', 'qml')
