import sys
from PyQt5 import QtQml

import pyqt5_tools.examples.exampleqmlitem


class ExampleQmlItemPlugin(QtQml.QQmlExtensionPlugin):
    def registerTypes(self, uri):
        sys.stderr.write('exampleqmlitemplugin.py debug: ExampleQmlItemPlugin.registerTypes(): uri - {!r}'.format(uri))
        QtQml.qmlRegisterType(
            pyqt5_tools.examples.exampleqmlitem.ExampleQmlItem,
            'examples',
            1,
            0,
            'ExampleQmlItem',
        )
