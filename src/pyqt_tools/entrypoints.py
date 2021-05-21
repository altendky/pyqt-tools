import os
import pathlib
import shutil
import subprocess
import sys
import sysconfig

import click
import dotenv

from . import _import_it
from . import major

PyQt = _import_it('PyQt')
qt_tools = _import_it('qt_tools')
pyqt_plugins = _import_it('pyqt_plugins')
_import_it('pyqt_plugins', 'utilities')
_import_it('pyqt_plugins', 'badplugin')
_import_it('pyqt_plugins', 'examplebuttonplugin')
_import_it('pyqt_plugins', 'examples')
_import_it('pyqt_plugins', 'examples', 'exampleqmlitem')
_import_it('pyqt_plugins', 'tests', 'testbutton')



here = pathlib.Path(__file__).parent
example_path = str(
    pathlib.Path(pyqt_plugins.examplebuttonplugin.__file__).parent,
)
bad_path = str(
    pathlib.Path(pyqt_plugins.badplugin.__file__).parent,
)

pyqt_root = pathlib.Path(PyQt.__file__).parent

maybe_extension = {
    'linux': lambda name: name,
    'win32': lambda name: '{}.exe'.format(name),
    'darwin': lambda name: name,
}[sys.platform]


def load_dotenv():
    env_path = dotenv.find_dotenv(usecwd=True)

    if len(env_path) == 0:
        return

    os.environ['DOT_ENV_DIRECTORY'] = pyqt_plugins.utilities.fspath(
        pathlib.Path(env_path).parent,
    )
    os.environ['SITE_PACKAGES'] = sysconfig.get_path('platlib')
    dotenv.load_dotenv(dotenv_path=env_path, interpolate=True, override=True)


@click.group()
def main():
    pass


@main.command()
def installuic():
    destination = qt_tools.bin_path()
    scripts_path = pathlib.Path(sysconfig.get_path("scripts"))

    shutil.copy(
        src=pyqt_plugins.utilities.fspath(
            scripts_path.joinpath(maybe_extension('pyuic{}'.format(major))),
        ),
        dst=pyqt_plugins.utilities.fspath(
            destination.joinpath(maybe_extension('uic')),
        ),
    )


qt_debug_plugins_option = click.option(
    '--qt-debug-plugins/--no-qt-debug-plugins',
    help='Set QT_DEBUG_PLUGINS=1',
)


@main.command(
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
    help='Include the path for the pyqt{major}-tools example button ({path})'.format(
        major=major,
        path=example_path,
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
def designer(
        ctx,
        widget_paths,
        designer_help,
        example_widget_path,
        test_exception_dialog,
        qt_debug_plugins
):
    # here for now at least since it still mutates
    load_dotenv()
    env = pyqt_plugins.create_environment(reference=os.environ)

    extras = []
    widget_paths = list(widget_paths)

    if designer_help:
        extras.append('--help')

    if example_widget_path:
        widget_paths.append(example_path)

    if test_exception_dialog:
        widget_paths.append(bad_path)

    env.update(pyqt_plugins.utilities.add_to_env_var_path_list(
        env=env,
        name='PYQTDESIGNERPATH',
        before=widget_paths,
        after=[''],
    ))

    if qt_debug_plugins:
        env['QT_DEBUG_PLUGINS'] = '1'

    pyqt_plugins.utilities.print_environment_variables(
        env,
        *pyqt_plugins.utilities.diagnostic_variables_to_print,
    )

    command_elements = qt_tools.create_command_elements(
        name='designer',
        sys_platform=sys.platform,
    )

    command = [*command_elements, *extras, *ctx.args]

    return subprocess.call(command, env=env)


qml2_import_path_option = click.option(
    '--qml2-import-path',
    '-p',
    'qml2_import_paths',
    help='Paths to be combined with QML2_IMPORT_PATH',
    type=click.Path(exists=True, file_okay=False, resolve_path=True),
    multiple=True,
)


@main.command(
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
    help='Run the pyqt{major}-tools QML example'.format(major=major),
    is_flag=True,
)
def qmlscene(
        ctx,
        qml2_import_paths,
        qmlscene_help,
        qt_debug_plugins,
        run_qml_example,
):
    # here for now at least since it still mutates
    load_dotenv()
    env = pyqt_plugins.create_environment(os.environ)
    extras = []

    if qmlscene_help:
        extras.append('--help')

    if run_qml_example:
        qml2_import_paths = qml2_import_paths + (pyqt_plugins.utilities.fspath(here),)
        extras.append(pyqt_plugins.utilities.fspath(
            pathlib.Path(pyqt_plugins.examples.__file__).parent / 'qmlapp.qml'
        ))

    pyqt_plugins.utilities.mutate_qml_path(env, paths=qml2_import_paths)

    if qt_debug_plugins:
        env['QT_DEBUG_PLUGINS'] = '1'

    pyqt_plugins.utilities.print_environment_variables(
        env,
        *pyqt_plugins.utilities.diagnostic_variables_to_print,
    )

    command_elements = qt_tools.create_command_elements(
        name='qmlscene',
        sys_platform=sys.platform,
    )

    command = [*command_elements, *extras, *ctx.args]

    return subprocess.call(command, env=env)


@main.command(
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
    help='Test the pyqt{major}-tools QML example'.format(major=major),
    is_flag=True,
)
def qmltestrunner(
        ctx,
        qml2_import_paths,
        qmltestrunner_help,
        qt_debug_plugins,
        test_qml_example,
):
    # here for now at least since it still mutates
    load_dotenv()
    env = pyqt_plugins.create_environment(os.environ)
    extras = []

    if qmltestrunner_help:
        extras.append('--help')

    if test_qml_example:
        qml2_import_paths = qml2_import_paths + (pyqt_plugins.utilities.fspath(here),)
        extras.extend([
            '-input',
            pyqt_plugins.utilities.fspath(
                pathlib.Path(pyqt_plugins.examples.__file__).parent / 'qmltest.qml'
            ),
        ])

    pyqt_plugins.utilities.mutate_qml_path(env, paths=qml2_import_paths)

    if qt_debug_plugins:
        env['QT_DEBUG_PLUGINS'] = '1'

    pyqt_plugins.utilities.print_environment_variables(
        env,
        *pyqt_plugins.utilities.diagnostic_variables_to_print,
    )

    command_elements = qt_tools.create_command_elements(
        name='qmltestrunner',
        sys_platform=sys.platform,
    )

    command = [*command_elements, *extras, *ctx.args]

    return subprocess.call(command, env=env)
