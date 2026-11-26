import os
import pathlib

from .. import import_it
from .. import major

QtCore = import_it("PyQt", "QtCore")
QtQuick = import_it("PyQt", "QtQuick")

test_path_env_var = 'PYQT{}TOOLS_TEST_PATH'.format(major)
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
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open('ab') as f:
                f.write(test_file_contents)

        return 'pass the test'

    @QtCore.pyqtProperty('QString')
    def other_value(self):
        pass

    @other_value.setter
    def other_value(self, value):
        pass

    def paint(self, painter):
        global write_for_test

        if write_for_test:
            write_for_test = False

            path = pathlib.Path(os.environ[test_path_env_var])
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open('ab') as f:
                f.write(test_file_contents)

        painter.drawText(
            int(self.width() / 2),
            int(self.height() / 2),
            'pyqt{}-tools'.format(major),
        )
