import importlib.util
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

# pyqt-plugins is only installed with the plugins extra.
if importlib.util.find_spec('pyqt{}_plugins'.format(major)) is None:
    pyqt_plugins = None
else:
    pyqt_plugins = _import_it('pyqt_plugins')
    _import_it('pyqt_plugins', 'badplugin')
    _import_it('pyqt_plugins', 'excepthook')
    _import_it('pyqt_plugins', 'examplebuttonplugin')
    _import_it('pyqt_plugins', 'examples')
    _import_it('pyqt_plugins', 'examples', 'exampleqmlitem')
    _import_it('pyqt_plugins', 'tests', 'testbutton')

plugins_requirement = 'pyqt{}-tools[plugins]'.format(major)


here = pathlib.Path(__file__).parent

if pyqt_plugins is None:
    example_path = None
    bad_path = None
    excepthook_path = None
else:
    example_path = str(
        pathlib.Path(pyqt_plugins.examplebuttonplugin.__file__).parent,
    )
    bad_path = str(
        pathlib.Path(pyqt_plugins.badplugin.__file__).parent,
    )
    excepthook_path = str(
        pathlib.Path(pyqt_plugins.excepthook.__file__).parent,
    )

pyqt_root = pathlib.Path(PyQt.__file__).parent

maybe_extension = {
    'linux': lambda name: name,
    'win32': lambda name: '{}.exe'.format(name),
    'darwin': lambda name: name,
}[sys.platform]


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


def create_environment():
    if pyqt_plugins is None:
        return qt_tools.create_environment(reference=os.environ)

    return pyqt_plugins.create_environment(reference=os.environ)


def mutate_qml_path(env, paths):
    paths = list(paths)

    if pyqt_plugins is not None:
        paths.append(os.fspath(pyqt_plugins.pyqt_qml_path))

    if len(paths) == 0:
        return

    env.update(add_to_env_var_path_list(
        env=env,
        name='QML2_IMPORT_PATH',
        before=paths,
        after=[''],
    ))


def require_plugins(options):
    used = [name for name, value in options.items() if value]

    if pyqt_plugins is None and len(used) > 0:
        raise click.UsageError(
            'The plugins extra is needed for {options}.'
            '  Install it with: pip install "{requirement}"'.format(
                options=', '.join(used),
                requirement=plugins_requirement,
            ),
        )


def plugins_help(text):
    if pyqt_plugins is None:
        return '{} (requires {})'.format(text.rstrip('.'), plugins_requirement)

    return text


def load_dotenv():
    env_path = dotenv.find_dotenv(usecwd=True)

    if len(env_path) == 0:
        return

    os.environ['DOT_ENV_DIRECTORY'] = os.fspath(
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
        src=os.fspath(
            scripts_path.joinpath(maybe_extension('pyuic{}'.format(major))),
        ),
        dst=os.fspath(
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
    help=plugins_help('Paths to be combined with PYQTDESIGNERPATH'),
    type=click.Path(exists=True, file_okay=False, resolve_path=True),
    multiple=True,
)
@click.option(
    '--example-widget-path',
    help=plugins_help(
        'Include the path for the pyqt{major}-tools example button{path}'.format(
            major=major,
            path='' if example_path is None else ' ({})'.format(example_path),
        ),
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
    help=plugins_help(
        'Raise an exception to check the exception dialog functionality.',
    ),
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
    require_plugins({
        '--widget-path': widget_paths,
        '--example-widget-path': example_widget_path,
        '--test-exception-dialog': test_exception_dialog,
    })

    # here for now at least since it still mutates
    load_dotenv()
    env = create_environment()

    extras = []
    widget_paths = list(widget_paths)

    if designer_help:
        extras.append('--help')

    if example_widget_path:
        widget_paths.append(example_path)

    if test_exception_dialog:
        widget_paths.append(bad_path)

    if pyqt_plugins is not None:
        env.update(add_to_env_var_path_list(
            env=env,
            name='PYQTDESIGNERPATH',
            # First, so that exceptions from all the other plugins get a dialog.
            before=[excepthook_path, *widget_paths],
            after=[''],
        ))

    if qt_debug_plugins:
        env['QT_DEBUG_PLUGINS'] = '1'

    print_environment_variables(env, *diagnostic_variables_to_print)

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
    help=plugins_help(
        'Run the pyqt{major}-tools QML example'.format(major=major),
    ),
    is_flag=True,
)
def qmlscene(
        ctx,
        qml2_import_paths,
        qmlscene_help,
        qt_debug_plugins,
        run_qml_example,
):
    require_plugins({'--run-qml-example': run_qml_example})

    # here for now at least since it still mutates
    load_dotenv()
    env = create_environment()
    extras = []

    if qmlscene_help:
        extras.append('--help')

    if run_qml_example:
        qml2_import_paths = qml2_import_paths + (os.fspath(here),)
        extras.append(os.fspath(
            pathlib.Path(pyqt_plugins.examples.__file__).parent / 'qmlapp.qml'
        ))

    mutate_qml_path(env, paths=qml2_import_paths)

    if qt_debug_plugins:
        env['QT_DEBUG_PLUGINS'] = '1'

    print_environment_variables(env, *diagnostic_variables_to_print)

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
    help=plugins_help(
        'Test the pyqt{major}-tools QML example'.format(major=major),
    ),
    is_flag=True,
)
def qmltestrunner(
        ctx,
        qml2_import_paths,
        qmltestrunner_help,
        qt_debug_plugins,
        test_qml_example,
):
    require_plugins({'--test-qml-example': test_qml_example})

    # here for now at least since it still mutates
    load_dotenv()
    env = create_environment()
    extras = []

    if qmltestrunner_help:
        extras.append('--help')

    if test_qml_example:
        qml2_import_paths = qml2_import_paths + (os.fspath(here),)
        extras.extend([
            '-input',
            os.fspath(
                pathlib.Path(pyqt_plugins.examples.__file__).parent / 'qmltest.qml'
            ),
        ])

    mutate_qml_path(env, paths=qml2_import_paths)

    if qt_debug_plugins:
        env['QT_DEBUG_PLUGINS'] = '1'

    print_environment_variables(env, *diagnostic_variables_to_print)

    command_elements = qt_tools.create_command_elements(
        name='qmltestrunner',
        sys_platform=sys.platform,
    )

    command = [*command_elements, *extras, *ctx.args]

    return subprocess.call(command, env=env)
