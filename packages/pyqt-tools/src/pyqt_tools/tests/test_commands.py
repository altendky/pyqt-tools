"""Tests that run with or without the plugins extra installed."""

import os
import pathlib
import subprocess
import sys
import sysconfig

import click.testing
import pytest

from .. import _import_it
from .. import entrypoints
from .. import major


qt_tools = _import_it('qt_tools')

scripts_path = pathlib.Path(sysconfig.get_path("scripts"))

without_plugins = pytest.mark.skipif(
    entrypoints.pyqt_plugins is not None,
    reason='pyqt{}-plugins is installed'.format(major),
)


@pytest.fixture(
    name="executable_cmd",
    params=[
        [os.fspath(scripts_path.joinpath("pyqt{}-tools".format(major)))],
        [os.fspath(scripts_path.joinpath("pyqt{}-toolsw".format(major)))],
        [sys.executable, "-m", "pyqt{}_tools".format(major)],
    ],
    ids=lambda cmd: pathlib.Path(cmd[0]).name,
)
def executable_cmd_fixture(request):
    return request.param


@pytest.fixture(name='calls')
def calls_fixture(monkeypatch, tmp_path):
    """Record the commands that would be run instead of running them."""
    calls = []

    def call(command, env):
        calls.append((command, env))
        return 0

    monkeypatch.setattr(subprocess, 'call', call)
    # Keep any .env file from being loaded.
    monkeypatch.chdir(tmp_path)
    for name in ['PYQTDESIGNERPATH', 'QML2_IMPORT_PATH', 'QT_PLUGIN_PATH']:
        monkeypatch.delenv(name, raising=False)

    return calls


def test_designer_runs(executable_cmd):
    with pytest.raises(subprocess.TimeoutExpired):
        subprocess.run(
            [*executable_cmd, 'designer'],
            check=True,
            timeout=40,
        )


def test_installuic_runs(executable_cmd):
    subprocess.run(
        [*executable_cmd, 'installuic'],
        check=True,
        timeout=40,
    )


@without_plugins
@pytest.mark.parametrize(
    argnames='application',
    argvalues=['designer', 'qmlscene', 'qmltestrunner'],
)
def test_no_plugin_paths_without_plugins(calls, application):
    result = click.testing.CliRunner().invoke(
        entrypoints.main,
        [application],
        catch_exceptions=False,
    )

    assert result.exit_code == 0
    [(command, env)] = calls
    assert command == qt_tools.create_command_elements(name=application)
    assert 'PYQTDESIGNERPATH' not in env
    assert 'QML2_IMPORT_PATH' not in env
    assert 'QT_PLUGIN_PATH' not in env


@without_plugins
@pytest.mark.parametrize(
    argnames='application',
    argvalues=['qmlscene', 'qmltestrunner'],
)
def test_qml2_import_path_without_plugins(calls, tmp_path, application):
    import_path = tmp_path / 'imports'
    import_path.mkdir()

    result = click.testing.CliRunner().invoke(
        entrypoints.main,
        [application, '--qml2-import-path', os.fspath(import_path)],
        catch_exceptions=False,
    )

    assert result.exit_code == 0
    [(command, env)] = calls
    paths = env['QML2_IMPORT_PATH'].split(os.pathsep)
    assert paths[0] == os.fspath(import_path.resolve())


@without_plugins
@pytest.mark.parametrize(
    argnames='arguments',
    argvalues=[
        ['designer', '--widget-path', '.'],
        ['designer', '--example-widget-path'],
        ['designer', '--test-exception-dialog'],
        ['qmlscene', '--run-qml-example'],
        ['qmltestrunner', '--test-qml-example'],
    ],
    ids=lambda arguments: ' '.join(arguments),
)
def test_plugin_options_need_the_extra(calls, arguments):
    result = click.testing.CliRunner().invoke(
        entrypoints.main,
        arguments,
        catch_exceptions=False,
    )

    assert result.exit_code == 2
    assert calls == []
    assert arguments[1] in result.output
    assert 'pip install "pyqt{}-tools[plugins]"'.format(major) in result.output
