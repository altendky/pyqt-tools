from PyQt5 import QtDesigner

import pyqt5_tools.examplebutton


class ExampleButtonPlugin(QtDesigner.QPyDesignerCustomWidgetPlugin):
    # https://wiki.python.org/moin/PyQt/Using_Python_Custom_Widgets_in_Qt_Designer

    def __init__(self, parent=None):
        parent.__init__(parent=parent)

        self.initialized = False

    def initialize(self, core):
        if self.initialized:
            return

        self.initialized = True

    def isInitialized(self):
        return self.initialized

    def createWidget(self, parent):
        return pyqt5_tools.examplebutton.ExampleButton(parent)

    def name(self):
        return 'pyqt5-tools Example Button Name'

    def group(self):
        return 'pyqt5_tools'

    def icon(self):
        QtDesigner.QPyDesignerCustomWidgetPlugin.icon(self)

    def toolTip(self):
        return 'pyqt5-tools Example Button Tool Tip'

    def whatsThis(self):
        return 'pyqt5-tools Example Button What\'s this'

    def isContainer(self):
        return False

    def includeFile(self):
        return 'pyqt5_tools.examplebutton'
