import sys
sys.stderr.write('exampleqmlitemplugin.py debug: : just imported sys\n')
sys.stderr.flush()
import traceback
sys.stderr.write('exampleqmlitemplugin.py debug: : just imported traceback\n')
sys.stderr.flush()

# TODO: CAMPid 0970432108721340872130742130870874321
import importlib

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


QtQml = import_it("PyQt", "QtQml")
sys.stderr.write('exampleqmlitemplugin.py debug: : just imported QtQml\n')
sys.stderr.flush()

pyqt_plugins = import_it("pyqt_plugins")
import_it("pyqt_plugins", "examples", "exampleqmlitem")
sys.stderr.write('exampleqmlitemplugin.py debug: : just imported pyqt{}_plugins.examples.exampleqmlitem\n'.format(major))
sys.stderr.flush()


class ExampleQmlItemPlugin(QtQml.QQmlExtensionPlugin):
    def registerTypes(self, uri):
        sys.stderr.write('exampleqmlitemplugin.py debug: ExampleQmlItemPlugin.registerTypes(): uri - {!r}\n'.format(uri))
        sys.stderr.flush()
        try:
            QtQml.qmlRegisterType(
                pyqt_plugins.examples.exampleqmlitem.ExampleQmlItem,
                'examples',
                1,
                0,
                'ExampleQmlItem',
            )
        except Exception as e:
            sys.stderr.write('exampleqmlitemplugin.py debug: ExampleQmlItemPlugin.registerTypes(): exception - {!r}\n'.format(e))
            sys.stderr.flush()
            traceback.print_exc(file=sys.stderr)
            sys.stderr.flush()
            raise

        sys.stderr.write('exampleqmlitemplugin.py debug: ExampleQmlItemPlugin.registerTypes(): about to return None\n')
        sys.stderr.flush()
        return None


sys.stderr.write('exampleqmlitemplugin.py debug: : import complete\n')
sys.stderr.flush()
