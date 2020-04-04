import sys
sys.stderr.write('exampleqmlitemplugin.py debug: : just imported sys')
from PyQt5 import QtQml
sys.stderr.write('exampleqmlitemplugin.py debug: : just imported QtQml')

import pyqt5_tools.examples.exampleqmlitem
sys.stderr.write('exampleqmlitemplugin.py debug: : just imported pyqt5_tools.examples.exampleqmlitem')


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

sys.stderr.write('exampleqmlitemplugin.py debug: : import complete')
