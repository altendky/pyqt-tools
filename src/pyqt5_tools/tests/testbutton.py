import os
import pathlib

from PyQt5 import QtWidgets


test_path_env_var = 'PYQT5TOOLS_TEST_PATH'
test_file_contents = b'heffalump'
write_for_test = test_path_env_var in os.environ


class TestButton(QtWidgets.QPushButton):
    def __init__(self, parent):
        global write_for_test

        super().__init__(parent)

        self.setText('pyqt5-tools Test Button')

        if write_for_test:
            write_for_test = False

            path = pathlib.Path(os.environ[test_path_env_var])
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open('ab') as f:
                f.write(test_file_contents)
