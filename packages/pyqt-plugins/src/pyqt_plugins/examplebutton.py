from . import import_it
from . import major

QtWidgets = import_it("PyQt", "QtWidgets")


class ExampleButton(QtWidgets.QPushButton):
    def __init__(self, parent):
        super().__init__(parent)

        self.setText('pyqt{}-tools Example Button'.format(major))
