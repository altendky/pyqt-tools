# TODO: CAMPid 0970432108721340872130742130870874321
import importlib
import pkg_resources

major = None


def import_it(*segments):
    global major

    if major is None:
        options = [5, 6]
    else:
        options = [major]

    error = None
    for major in options:
        # TODO: this is not great but the plugin gets imported directly rather
        #       than as part of the module so...  could add some code here on
        #       build or something.  but yeah, all kind of a mess.  require an
        #       env var be set, etc.
        try:
            m = {
                "pyqt_tools": "pyqt{major}_tools".format(major=major),
                "pyqt_plugins": "pyqt{major}_plugins".format(major=major),
                "qt_tools": "qt{major}_tools".format(major=major),
                "qt_applications": "qt{major}_applications".format(major=major),
                "PyQt": "PyQt{major}".format(major=major),
            }

            majored = [m[segments[0]], *segments[1:]]
            return importlib.import_module(".".join(majored))
        except ModuleNotFoundError as e:
            if error is None:
                error = e
                continue
            else:
                raise e from error


qt_tools = import_it("qt_tools")
QtGui = import_it("PyQt", "QtGui")
QtDesigner = import_it("PyQt", "QtDesigner")
pyqt_plugins = import_it("pyqt_plugins")
import_it("pyqt_plugins", "tests", "testbutton")


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
        return pyqt_plugins.tests.testbutton.TestButton(parent)

    def name(self):
        return pyqt_plugins.tests.testbutton.TestButton.__name__

    def group(self):
        return 'pyqt{}-tools'.format(major)

    def icon(self):
        return QtGui.QIcon()

    def toolTip(self):
        return 'pyqt{}-tools Test Button Tool Tip'.format(major)

    def whatsThis(self):
        return 'pyqt{}-tools Test Button What\'s this'.format(major)

    def isContainer(self):
        return False

    def includeFile(self):
        return 'pyqt{}_plugins.tests.testbutton'.format(major)
