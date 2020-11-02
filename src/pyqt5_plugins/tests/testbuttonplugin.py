from PyQt5 import QtGui, QtDesigner

import pyqt5_plugins.tests.testbutton


class TestButtonPlugin(QtDesigner.QPyDesignerCustomWidgetPlugin):
    # https://wiki.python.org/moin/PyQt/Using_Python_Custom_Widgets_in_Qt_Designer

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.initialized = False

    def initialize(self, core):
        if self.initialized:
            return

        self.initialized = True

    def isInitialized(self):
        return self.initialized

    def createWidget(self, parent):
        return pyqt5_plugins.tests.testbutton.TestButton(parent)

    def name(self):
        return pyqt5_plugins.tests.testbutton.TestButton.__name__

    def group(self):
        return 'pyqt5-tools'

    def icon(self):
        return QtGui.QIcon()

    def toolTip(self):
        return 'pyqt5-tools Test Button Tool Tip'

    def whatsThis(self):
        return 'pyqt5-tools Test Button What\'s this'

    def isContainer(self):
        return False

    def includeFile(self):
        return 'pyqt5_plugins.tests.testbutton'
