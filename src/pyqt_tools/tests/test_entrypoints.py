import os
import pathlib
import subprocess
import sys
import sysconfig

import pytest

from .. import _import_it
from .. import major
from .. import version
from .. import string_version


qt_tools = _import_it('qt_tools')
pyqt_plugins = _import_it('pyqt_plugins')
_import_it('pyqt_plugins', 'examples', 'exampleqmlitem')
_import_it('pyqt_plugins', 'tests', 'testbutton')
_import_it('pyqt_plugins', 'tests', 'testbuttonplugin')
_import_it('pyqt_plugins', 'utilities')


fspath = getattr(os, 'fspath', str)

scripts_path = pathlib.Path(sysconfig.get_path("scripts"))
executable_path_string = fspath(scripts_path.joinpath("pyqt{}-tools".format(major)))

vars_to_print = [
    *pyqt_plugins.utilities.diagnostic_variables_to_print,
    pyqt_plugins.examples.exampleqmlitem.test_path_env_var,
    pyqt_plugins.tests.testbutton.test_path_env_var,
]


@pytest.fixture(name='environment')
def environment_fixture():
    environment = pyqt_plugins.create_environment(os.environ)
    pyqt_plugins.utilities.mutate_qml_path(environment, paths=qml2_import_paths)
    environment['QT_DEBUG_PLUGINS'] = '1'

    return environment


def test_designer_creates_test_widget(tmp_path, environment):
    file_path = tmp_path/'tigger'
    environment[pyqt_plugins.tests.testbutton.test_path_env_var] = fspath(file_path)

    widget_plugin_path = pathlib.Path(
        pyqt_plugins.tests.testbuttonplugin.__file__,
    ).parent

    environment.update(pyqt_plugins.utilities.add_to_env_var_path_list(
        env=environment,
        name='PYQTDESIGNERPATH',
        before=[fspath(widget_plugin_path)],
        after=[''],
    ))

    pyqt_plugins.utilities.print_environment_variables(environment, *vars_to_print)

    with pytest.raises(subprocess.TimeoutExpired):
        subprocess.run(
            [
                executable_path_string,
                'designer',
            ],
            check=True,
            env=environment,
            timeout=40,
        )

    assert (
            file_path.read_bytes()
            == pyqt_plugins.tests.testbutton.test_file_contents
    )


qml2_import_paths = (pyqt_plugins.utilities.fspath(pyqt_plugins.root),)


# https://www.riverbankcomputing.com/pipermail/pyqt/2021-May/043916.html
@pytest.mark.skipif(
    (6,) <= version <= (6, 1, 0),
    reason="QML not supported for v6 through v6.1.0: {}".format(string_version),
)
# https://github.com/altendky/pyqt-tools/issues/110#issuecomment-1483673605
@pytest.mark.xfail(
    version[0] == 5 and sys.platform == "win32" and sys.version_info[:2] == (3, 11),
    reason="accepting failure until we figure out the problem".format(string_version),
    strict=True,
)
def test_qmlscene_paints_test_item(tmp_path, environment):
    file_path = tmp_path/'eeyore'
    environment[pyqt_plugins.examples.exampleqmlitem.test_path_env_var] = fspath(file_path)

    qml_example_path = pyqt_plugins.utilities.fspath(
        pathlib.Path(pyqt_plugins.examples.__file__).parent / 'qmlapp.qml'
    )

    pyqt_plugins.utilities.print_environment_variables(environment, *vars_to_print)

    with pytest.raises(subprocess.TimeoutExpired):
        subprocess.run(
            [
                fspath(qt_tools.application_path('qmlscene')),
                fspath(qml_example_path),
            ],
            check=True,
            env=environment,
            timeout=40,
        )

    assert (
            file_path.read_bytes()
            == pyqt_plugins.examples.exampleqmlitem.test_file_contents
    )


# https://www.riverbankcomputing.com/pipermail/pyqt/2021-May/043916.html
@pytest.mark.skipif(
    (6,) <= version <= (6, 1, 0),
    reason="QML not supported for v6 through v6.1.0: {}".format(string_version),
)
# https://github.com/altendky/pyqt-tools/issues/110#issuecomment-1483673605
@pytest.mark.xfail(
    version[0] == 5 and sys.platform == "win32" and sys.version_info[:2] == (3, 11),
    reason="accepting failure until we figure out the problem".format(string_version),
    strict=True,
)
def test_qmltestrunner_paints_test_item(tmp_path, environment):
    file_path = tmp_path/'piglet'
    environment[pyqt_plugins.examples.exampleqmlitem.test_path_env_var] = fspath(file_path)

    qml_test_path = pyqt_plugins.utilities.fspath(
        pathlib.Path(pyqt_plugins.examples.__file__).parent / 'qmltest.qml'
    )

    pyqt_plugins.utilities.print_environment_variables(environment, *vars_to_print)

    subprocess.run(
        [
            executable_path_string,
            'qmltestrunner',
            '--',
            '-input',
            qml_test_path,
        ],
        check=True,
        env=environment,
        timeout=40,
    )

    assert (
            file_path.read_bytes()
            == pyqt_plugins.examples.exampleqmlitem.test_file_contents
    )


def test_installuic_does_not_fail(environment):
    pyqt_plugins.utilities.print_environment_variables(environment, *vars_to_print)

    subprocess.run(
        [
            executable_path_string,
            'installuic',
        ],
        check=True,
        env=environment,
        timeout=40,
    )
