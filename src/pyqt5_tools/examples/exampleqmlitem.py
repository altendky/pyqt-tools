import os
import pathlib

from PyQt5 import QtCore
from PyQt5 import QtQuick

test_path_env_var = 'PYQT5TOOLS_TEST_PATH'
test_file_contents = b'jagular'
write_for_test = test_path_env_var in os.environ


class ExampleQmlItem(QtQuick.QQuickPaintedItem):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @QtCore.pyqtProperty('QString')
    def test_value(self):
        global write_for_test

        if write_for_test:
            write_for_test = False

            path = pathlib.Path(os.environ[test_path_env_var])
            with path.open('xb') as f:
                f.write(test_file_contents)

        return 'pass the test'

    @QtCore.pyqtProperty('QString')
    def other_value(self):
        pass

    @other_value.setter
    def other_value(self, value):
        pass

    def paint(self, painter):
        painter.drawText(
            self.width() / 2,
            self.height() / 2,
            'pyqt5-tools',
        )
