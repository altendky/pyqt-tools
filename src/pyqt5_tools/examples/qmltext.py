from PyQt5 import QtQuick


class Text(QtQuick.QQuickPaintedItem):
    def paint(self, painter):
        painter.drawText(0, 0, 'pyqt5-tools')
