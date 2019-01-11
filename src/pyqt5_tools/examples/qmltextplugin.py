from PyQt5 import QtQml

import pyqt5_tools.examples.qmltext


class Plugin(QtQml.QQmlExtensionPlugin):
    def registerTypes(self, uri):
        QtQml.qmlRegisterType(
            pyqt5_tools.examples.qmltext.Text,
            'examples',
            1,
            0,
            'Text',
        )
