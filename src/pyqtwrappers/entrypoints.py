import os
import pathlib
import shutil
import subprocess
import sys

import click
import qttools

import pyqtplugins.utilities
import pyqtplugins.badplugin
import pyqtplugins.examplebuttonplugin
import pyqtplugins.examples
import pyqtplugins.examples.exampleqmlitem
import pyqtplugins.tests.testbutton


here = pathlib.Path(__file__).parent
bin = here/'Qt'/'bin'
example_path = str(
    pathlib.Path(pyqtplugins.examplebuttonplugin.__file__).parent,
)
bad_path = str(
    pathlib.Path(pyqtplugins.badplugin.__file__).parent,
)

maybe_extension = {
    'linux': lambda name: name,
    'win32': lambda name: '{}.exe'.format(name),
    'darwin': lambda name: name,
}[sys.platform]


def pyqttoolsinstalluic():
    destination = bin/'bin'
    destination.mkdir(parents=True, exist_ok=True)
    there = pathlib.Path(sys.executable).parent

    shutil.copy(
        src=str(there / maybe_extension('pyuic5')),
        dst=str(destination/maybe_extension('uic')),
    )


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
def pyqtdesigner(
        ctx,
        widget_paths,
        designer_help,
        example_widget_path,
        test_exception_dialog,
        qt_debug_plugins
):
    env = pyqtplugins.utilities.create_env(reference=os.environ)

    extras = []
    widget_paths = list(widget_paths)

    if designer_help:
        extras.append('--help')

    if example_widget_path:
        widget_paths.append(example_path)

    if test_exception_dialog:
        widget_paths.append(bad_path)

    env.update(pyqtplugins.utilities.add_to_env_var_path_list(
        env=env,
        name='PYQTDESIGNERPATH',
        before=widget_paths,
        after=[''],
    ))

    if qt_debug_plugins:
        env['QT_DEBUG_PLUGINS'] = '1'

    pyqtplugins.utilities.print_environment_variables(
        env,
        *pyqtplugins.utilities.diagnostic_variables_to_print,
    )

    command = [
        pyqtplugins.utilities.fspath(qttools.application_path('designer')),
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
def pyqtqmlscene(
        ctx,
        qml2_import_paths,
        qmlscene_help,
        qt_debug_plugins,
        run_qml_example,
):
    env = pyqtplugins.utilities.create_env(os.environ)
    extras = []

    if qmlscene_help:
        extras.append('--help')

    if run_qml_example:
        qml2_import_paths = qml2_import_paths + (pyqtplugins.utilities.fspath(here),)
        extras.append(pyqtplugins.utilities.fspath(
            pathlib.Path(pyqtplugins.examples.__file__).parent / 'qmlapp.qml'
        ))

    pyqtplugins.utilities.mutate_qml_path(env, paths=qml2_import_paths)

    if qt_debug_plugins:
        env['QT_DEBUG_PLUGINS'] = '1'

    pyqtplugins.utilities.print_environment_variables(
        env,
        *pyqtplugins.utilities.diagnostic_variables_to_print,
    )

    command = [
        pyqtplugins.utilities.fspath(qttools.application_path('qmlscene')),
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
def pyqtqmltestrunner(
        ctx,
        qml2_import_paths,
        qmltestrunner_help,
        qt_debug_plugins,
        test_qml_example,
):
    env = pyqtplugins.utilities.create_env(os.environ)
    extras = []

    if qmltestrunner_help:
        extras.append('--help')

    if test_qml_example:
        qml2_import_paths = qml2_import_paths + (pyqtplugins.utilities.fspath(here),)
        extras.extend([
            '-input',
            pyqtplugins.utilities.fspath(
                pathlib.Path(pyqtplugins.examples.__file__).parent / 'qmltest.qml'
            ),
        ])

    pyqtplugins.utilities.mutate_qml_path(env, paths=qml2_import_paths)

    if qt_debug_plugins:
        env['QT_DEBUG_PLUGINS'] = '1'

    pyqtplugins.utilities.print_environment_variables(
        env,
        *pyqtplugins.utilities.diagnostic_variables_to_print,
    )

    command = [
        pyqtplugins.utilities.fspath(qttools.application_path('qmltestrunner')),
        *extras,
        *ctx.args,
    ]

    return subprocess.call(command, env=env)
