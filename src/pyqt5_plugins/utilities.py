import os
import pathlib
import sys
import sysconfig

import qt5_applications
import PyQt5

import pyqt5_plugins


fspath = getattr(os, 'fspath', str)


diagnostic_variables_to_print = [
    'DISPLAY',
    'LD_LIBRARY_PATH'
    'PYQTDESIGNERPATH',
    'PYTHONPATH',
    'PATH',
    'QML2_IMPORT_PATH',
    'QT_DEBUG_PLUGINS',
    'QT_PLUGIN_PATH',
]


def create_env(reference):
    environment = qt5_applications.create_environment(reference=reference)

    environment.update(add_to_env_var_path_list(
        env=environment,
        name='QT_PLUGIN_PATH',
        before=[],
        after=[fspath(pyqt5_plugins.pyqt5_plugins_path), fspath(pyqt5_plugins.plugins)],
    ))
    # TODO: maybe also
    # PyQt5.QtCore.QLibraryInfo.location(
    #    PyQt5.QtCore.QLibraryInfo.PluginsPath,
    # )

    environment.update(add_to_env_var_path_list(
        env=environment,
        name='PYTHONPATH',
        before=sys.path,
        after=[''],
    ))
    environment.update(add_to_env_var_path_list(
        env=environment,
        name='PATH',
        before=sys.path,
        after=[''],
    ))

    return environment


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
        before=[*paths, fspath(pyqt5_plugins.pyqt5_qml_path)],
        after=[''],
    ))
