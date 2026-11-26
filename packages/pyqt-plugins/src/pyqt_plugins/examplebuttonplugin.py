# TODO: CAMPid 0970432108721340872130742130870874321
import importlib
import pkg_resources

major = int(pkg_resources.get_distribution(__name__.partition('.')[0]).version.partition(".")[0])


def import_it(*segments):
    m = {
        "pyqt_tools": "pyqt{major}_tools".format(major=major),
        "pyqt_plugins": "pyqt{major}_plugins".format(major=major),
        "qt_tools": "qt{major}_tools".format(major=major),
        "qt_applications": "qt{major}_applications".format(major=major),
        "PyQt": "PyQt{major}".format(major=major),
    }

    majored = [m[segments[0]], *segments[1:]]
    return importlib.import_module(".".join(majored))


QtGui = import_it("PyQt", "QtGui")
QtDesigner = import_it("PyQt", "QtDesigner")
pyqt_plugins = import_it("pyqt_plugins")
import_it("pyqt_plugins", "examplebutton")


class ExampleButtonPlugin(QtDesigner.QPyDesignerCustomWidgetPlugin):
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
        return pyqt_plugins.examplebutton.ExampleButton(parent)

    def name(self):
        return pyqt_plugins.examplebutton.ExampleButton.__name__

    def group(self):
        return 'pyqt{}-tools'.format(major)

    def icon(self):
        return QtGui.QIcon()

    def toolTip(self):
        return 'pyqt{}-tools Example Button Tool Tip'.format(major)

    def whatsThis(self):
        return 'pyqt{}-tools Example Button What\'s this'.format(major)

    def isContainer(self):
        return False

    def includeFile(self):
        return 'pyqt{}_plugins.examplebutton'.format(major)
