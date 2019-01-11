from PyQt5 import QtGui
from PyQt5 import QtQuick


class Text(QtQuick.QQuickPaintedItem):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def paint(self, painter):
        painter.drawText(
            self.width() / 2, 
            self.height() / 2, 
            'pyqt5-tools',
        )
