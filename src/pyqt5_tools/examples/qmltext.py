import os
import pathlib

from PyQt5 import QtQuick


test_path_env_var = 'PYQT5TOOLS_TEST_PATH'
test_file_contents = b'jagular'
write_for_test = test_path_env_var in os.path


class Text(QtQuick.QQuickPaintedItem):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def paint(self, painter):
        global write_for_test

        if write_for_test:
            write_for_test = False

            path = pathlib.Path(os.environ[test_path_env_var])
            with path.open('xb') as f:
                f.write(test_file_contents)

        painter.drawText(
            self.width() / 2, 
            self.height() / 2, 
            'pyqt5-tools',
        )
