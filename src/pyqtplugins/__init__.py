import pathlib

import PyQt5


root = pathlib.Path(__file__).resolve().parent
plugins = root.joinpath('Qt', 'plugins')

pyqt5_root = pathlib.Path(PyQt5.__file__).resolve().parent
pyqt5_qml_path = pyqt5_root.joinpath('Qt', 'qml')
