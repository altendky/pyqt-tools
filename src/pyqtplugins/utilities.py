import os
import pathlib
import sys
import sysconfig

import PyQt5

import pyqtplugins


fspath = getattr(os, 'fspath', str)


def create_env(reference):
    # TODO: uck, mutating
    env = dict(reference)

    env.update(add_to_env_var_path_list(
        env=env,
        name='QT_PLUGIN_PATH',
        before=[],
        after=[fspath(pyqtplugins.here / 'Qt' / 'plugins')],
    ))
    # TODO: maybe also
    # PyQt5.QtCore.QLibraryInfo.location(
    #    PyQt5.QtCore.QLibraryInfo.PluginsPath,
    # )

    if sys.platform == 'linux':
        env.update(add_to_env_var_path_list(
            env=env,
            name='LD_LIBRARY_PATH',
            before=[''],
            after=[sysconfig.get_config_var('LIBDIR')],
        ))

    return env


def add_to_env_var_path_list(env, name, before, after):
    return {
        name: os.pathsep.join((
            *before,
            env.get(name, ''),
            *after
        ))
    }


def mutate_env_for_paths(env):
    env.update(add_to_env_var_path_list(
        env=env,
        name='PYTHONPATH',
        before=sys.path,
        after=[''],
    ))
    env.update(add_to_env_var_path_list(
        env=env,
        name='PATH',
        before=sys.path,
        after=[''],
    ))


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
        before=[*paths, fspath(pathlib.Path(PyQt5.__file__).parent/'Qt'/'qml')],
        after=[''],
    ))
