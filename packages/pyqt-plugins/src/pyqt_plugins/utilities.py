import os

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


pyqt_plugins = import_it("pyqt_plugins")


fspath = getattr(os, 'fspath', str)


diagnostic_variables_to_print = [
    'DISPLAY',
    'LD_LIBRARY_PATH',
    'DYLD_LIBRARY_PATH',
    'PYQTDESIGNERPATH',
    'PYTHONPATH',
    'PATH',
    'QML2_IMPORT_PATH',
    'QT_DEBUG_PLUGINS',
    'QT_PLUGIN_PATH',
]


def add_to_env_var_path_list(env, name, before, after):
    return {
        name: os.pathsep.join((
            *before,
            env.get(name, ''),
            *after
        ))
    }


def print_environment_variables(env, *variables):
    for name in variables:
        value = env.get(name)
        if value is None:
            print('{} is not set'.format(name))
        else:
            print('{}: {}'.format(name, value))


def mutate_qml_path(env, paths):
    env.update(add_to_env_var_path_list(
        env=env,
        name='QML2_IMPORT_PATH',
        before=[*paths, fspath(pyqt_plugins.pyqt_qml_path)],
        after=[''],
    ))
