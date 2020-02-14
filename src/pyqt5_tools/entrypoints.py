import os
import pathlib
import shutil
import subprocess
import sys
import sysconfig

import click
import dotenv

import pyqt5_tools.badplugin
import pyqt5_tools.examplebuttonplugin
import pyqt5_tools.examples

fspath = getattr(os, 'fspath', str)


here = pathlib.Path(__file__).parent
bin = here/'Qt'/'bin'
example_path = str(
    pathlib.Path(pyqt5_tools.examplebuttonplugin.__file__).parent,
)
bad_path = str(
    pathlib.Path(pyqt5_tools.badplugin.__file__).parent,
)

maybe_extension = {
    'linux': lambda name: name,
    'win32': lambda name: '{}.exe'.format(name),
    'darwin': lambda name: name,
}[sys.platform]


def pyqt5toolsinstalluic():
    destination = bin/'bin'
    destination.mkdir(parents=True, exist_ok=True)
    there = pathlib.Path(sys.executable).parent

    shutil.copy(
        src=str(there / maybe_extension('pyuic5')),
        dst=str(destination/maybe_extension('uic')),
    )


def load_dotenv():
    env_path = dotenv.find_dotenv(usecwd=True)
    if len(env_path) > 0:
        os.environ['DOT_ENV_DIRECTORY'] = str(pathlib.Path(env_path).parent)
        dotenv.load_dotenv(dotenv_path=env_path, override=True)


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


qt_debug_plugins_option = click.option(
    '--qt-debug-plugins/--no-qt-debug-plugins',
    help='Set QT_DEBUG_PLUGINS=1',
)


@click.command(
    context_settings={
        'ignore_unknown_options': True,
        'allow_extra_args': True,
    },
)
@click.pass_context
@click.option(
    '--widget-path',
    '-p',
    'widget_paths',
    help='Paths to be combined with PYQTDESIGNERPATH',
    type=click.Path(exists=True, file_okay=False, resolve_path=True),
    multiple=True,
)
@click.option(
    '--example-widget-path',
    help='Include the path for the pyqt5-tools example button ({})'.format(
        example_path,
    ),
    is_flag=True,
)
@click.option(
    '--designer-help',
    help='Pass through to get Designer\'s --help',
    is_flag=True,
)
@click.option(
    '--test-exception-dialog',
    help='Raise an exception to check the exception dialog functionality.',
    is_flag=True,
)
@qt_debug_plugins_option
def pyqt5designer(
        ctx,
        widget_paths,
        designer_help,
        example_widget_path,
        test_exception_dialog,
        qt_debug_plugins
):
    load_dotenv()

    extras = []
    widget_paths = list(widget_paths)

    if designer_help:
        extras.append('--help')

    if example_widget_path:
        widget_paths.append(example_path)

    if test_exception_dialog:
        widget_paths.append(bad_path)

    vars_to_print = [
        'PYQTDESIGNERPATH',
        'PYTHONPATH',
        'PATH',
        'QT_DEBUG_PLUGINS',
    ]

    env = dict(os.environ)
    env.update(add_to_env_var_path_list(
        env=env,
        name='PYQTDESIGNERPATH',
        before=widget_paths,
        after=[''],
    ))

    if sys.platform == 'linux':
        vars_to_print.append('LD_LIBRARY_PATH')
        env.update(add_to_env_var_path_list(
            env=env,
            name='LD_LIBRARY_PATH',
            before=[''],
            after=[sysconfig.get_config_var('LIBDIR')],
        ))

    mutate_env_for_paths(env)

    if qt_debug_plugins:
        env['QT_DEBUG_PLUGINS'] = '1'

    print_environment_variables(env, *vars_to_print)

    command = [
        str(bin / maybe_extension('designer')),
        *extras,
        *ctx.args,
    ]

    return subprocess.call(command, env=env)


qml2_import_path_option = click.option(
    '--qml2-import-path',
    '-p',
    'qml2_import_paths',
    help='Paths to be combined with QML2_IMPORT_PATH',
    type=click.Path(exists=True, file_okay=False, resolve_path=True),
    multiple=True,
)


def mutate_qml_path(env, paths):
    env.update(add_to_env_var_path_list(
        env=env,
        name='QML2_IMPORT_PATH',
        before=[*paths, str(here/'Qt'/'qml')],
        after=[''],
    ))


@click.command(
    context_settings={
        'ignore_unknown_options': True,
        'allow_extra_args': True,
    },
)
@click.pass_context
@qml2_import_path_option
@click.option(
    '--qmlscene-help',
    help='Pass through to get QML scene\'s --help',
    is_flag=True,
)
@qt_debug_plugins_option
@click.option(
    '--run-qml-example',
    help='Run the pyqt5-tools QML example',
    is_flag=True,
)
def pyqt5qmlscene(
        ctx,
        qml2_import_paths,
        qmlscene_help,
        qt_debug_plugins,
        run_qml_example,
):
    load_dotenv()
    extras = []

    if qmlscene_help:
        extras.append('--help')

    env = dict(os.environ)

    if run_qml_example:
        qml2_import_paths = qml2_import_paths + (fspath(here),)
        extras.append(fspath(
            pathlib.Path(pyqt5_tools.examples.__file__).parent/'qmlapp.qml'
        ))

    mutate_qml_path(env, paths=qml2_import_paths)
    mutate_env_for_paths(env)

    if qt_debug_plugins:
        env['QT_DEBUG_PLUGINS'] = '1'

    print_environment_variables(
        env,
        'QML2_IMPORT_PATH',
        'PYTHONPATH',
        'PATH',
        'QT_DEBUG_PLUGINS',
    )

    command = [
        str(bin / maybe_extension('qmlscene')),
        *extras,
        *ctx.args,
    ]

    return subprocess.call(command, env=env)


@click.command(
    context_settings={
        'ignore_unknown_options': True,
        'allow_extra_args': True,
    },
)
@click.pass_context
@qml2_import_path_option
@click.option(
    '--qmltestrunner-help',
    help='Pass through to get QML test runner\'s --help',
    is_flag=True,
)
@qt_debug_plugins_option
@click.option(
    '--test-qml-example',
    help='Test the pyqt5-tools QML example',
    is_flag=True,
)
def pyqt5qmltestrunner(
        ctx,
        qml2_import_paths,
        qmltestrunner_help,
        qt_debug_plugins,
        test_qml_example,
):
    load_dotenv()
    extras = []

    if qmltestrunner_help:
        extras.append('--help')

    env = dict(os.environ)

    if test_qml_example:
        qml2_import_paths = qml2_import_paths + (fspath(here),)
        extras.extend([
            '-input',
            fspath(
                pathlib.Path(pyqt5_tools.examples.__file__).parent/'qmltest.qml'
            ),
        ])

    mutate_qml_path(env, paths=qml2_import_paths)
    mutate_env_for_paths(env)

    if qt_debug_plugins:
        env['QT_DEBUG_PLUGINS'] = '1'

    print_environment_variables(
        env,
        'QML2_IMPORT_PATH',
        'PYTHONPATH',
        'PATH',
        'QT_DEBUG_PLUGINS',
    )

    command = [
        str(bin / maybe_extension('qmltestrunner')),
        *extras,
        *ctx.args,
    ]

    return subprocess.call(command, env=env)


# def designer():
#     load_dotenv()
#     return subprocess.call([str(here/'Qt'/'bin'/'designer.exe'), *sys.argv[1:]])
