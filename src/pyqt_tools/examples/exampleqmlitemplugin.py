import sys
sys.stderr.write('exampleqmlitemplugin.py debug: : just imported sys\n')
sys.stderr.flush()
import traceback
sys.stderr.write('exampleqmlitemplugin.py debug: : just imported traceback\n')
sys.stderr.flush()

from .. import _import_it

QtQml = _import_it('PyQt', 'QtQml')
sys.stderr.write('exampleqmlitemplugin.py debug: : just imported QtQml\n')
sys.stderr.flush()

pyqt_plugins = _import_it('pyqt_plugins')
_import_it('pyqt_plugins', 'examples', 'exampleqmlitem')
sys.stderr.write('exampleqmlitemplugin.py debug: : just imported pyqt5_tools.examples.exampleqmlitem\n')
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
