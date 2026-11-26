import os
import pathlib
import pkg_resources
import sys
import sysconfig

from ._version import get_versions
__version__ = get_versions()['version']
del get_versions

major = int(pkg_resources.get_distribution(__name__.partition('.')[0]).version.partition(".")[0])


# TODO: CAMPid 0970432108721340872130742130870874321
def import_it(*segments):
    import importlib

    m = {
        "pyqt_tools": "pyqt{major}_tools".format(major=major),
        "pyqt_plugins": "pyqt{major}_plugins".format(major=major),
        "qt_tools": "qt{major}_tools".format(major=major),
        "qt_applications": "qt{major}_applications".format(major=major),
        "PyQt": "PyQt{major}".format(major=major),
    }

    majored = [m[segments[0]], *segments[1:]]
    return importlib.import_module(".".join(majored))


qt_tools = import_it("qt_tools")
PyQt = import_it("PyQt")
import_it("PyQt", "QtCore")
pyqt_plugins = import_it("pyqt_plugins")
import_it("pyqt_plugins", "utilities")


pyqt_version = tuple(
    int(segment)
    for segment in PyQt.QtCore.PYQT_VERSION_STR.split('.')
)

root = pathlib.Path(__file__).resolve().parent
# TODO: so apparently qml wants it all lower case...
if sys.platform == 'win32':
    root = pathlib.Path(pyqt_plugins.utilities.fspath(root).lower())
plugins = root.joinpath('Qt', 'plugins')

pyqt_root = pathlib.Path(PyQt.__file__).resolve().parent
if pyqt_version >= (6,):
    pyqt_qt_root = pyqt_root.joinpath('Qt6')
elif pyqt_version >= (5, 15, 4):
    pyqt_qt_root = pyqt_root.joinpath('Qt5')
else:
    pyqt_qt_root = pyqt_root.joinpath('Qt')
pyqt_qml_path = pyqt_qt_root.joinpath('qml')
pyqt_plugins_path = pyqt_qt_root.joinpath('plugins')


def create_environment(reference=None):
    if reference is None:
        reference = dict(os.environ)
    environment = qt_tools.create_environment(reference=reference)

    if sys.platform in {'linux', 'darwin'}:
        if sys.platform == 'linux':
            variable = 'LD_LIBRARY_PATH'
        else:
            variable = 'DYLD_LIBRARY_PATH'
        environment.update(pyqt_plugins.utilities.add_to_env_var_path_list(
            env=environment,
            name=variable,
            before=[],
            after=[sysconfig.get_config_var('LIBDIR')],
        ))

    environment.update(pyqt_plugins.utilities.add_to_env_var_path_list(
        env=environment,
        name='QT_PLUGIN_PATH',
        before=[],
        after=[
            pyqt_plugins.utilities.fspath(pyqt_plugins_path),
            pyqt_plugins.utilities.fspath(plugins),
        ],
    ))
    # TODO: maybe also
    # PyQt.QtCore.QLibraryInfo.location(
    #    PyQt.QtCore.QLibraryInfo.PluginsPath,
    # )

    environment.update(pyqt_plugins.utilities.add_to_env_var_path_list(
        env=environment,
        name='PYTHONPATH',
        before=sys.path,
        after=[''],
    ))
    environment.update(pyqt_plugins.utilities.add_to_env_var_path_list(
        env=environment,
        name='PATH',
        before=sys.path,
        after=[''],
    ))

    return environment
