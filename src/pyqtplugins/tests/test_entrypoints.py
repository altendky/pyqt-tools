import os
import pathlib
import subprocess

import pytest
import qttools

import pyqtplugins.entrypoints
import pyqtplugins.examples.exampleqmlitem
import pyqtplugins.tests.testbutton
import pyqtplugins.tests.testbuttonplugin
import pyqtplugins.utilities


fspath = getattr(os, 'fspath', str)


vars_to_print = [
    *pyqtplugins.utilities.diagnostic_variables_to_print,
    pyqtplugins.examples.exampleqmlitem.test_path_env_var,
    pyqtplugins.tests.testbutton.test_path_env_var,
]


@pytest.fixture(name='environment')
def environment_fixture():
    environment = pyqtplugins.utilities.create_env(os.environ)
    pyqtplugins.utilities.mutate_qml_path(environment, paths=qml2_import_paths)
    environment['QT_DEBUG_PLUGINS'] = '1'

    return environment


def test_designer_creates_test_widget(tmp_path, environment):
    file_path = tmp_path/'tigger'
    environment[pyqtplugins.tests.testbutton.test_path_env_var] = fspath(file_path)

    widget_plugin_path = pathlib.Path(
        pyqtplugins.tests.testbuttonplugin.__file__,
    ).parent

    environment.update(pyqtplugins.utilities.add_to_env_var_path_list(
        env=environment,
        name='PYQTDESIGNERPATH',
        before=[fspath(widget_plugin_path)],
        after=[''],
    ))

    pyqtplugins.utilities.print_environment_variables(environment, *vars_to_print)

    with pytest.raises(subprocess.TimeoutExpired):
        subprocess.run(
            [fspath(qttools.application_path('designer'))],
            check=True,
            env=environment,
            timeout=20,
        )

    assert (
            file_path.read_bytes()
            == pyqtplugins.tests.testbutton.test_file_contents
    )


qml2_import_paths = (pyqtplugins.utilities.fspath(pyqtplugins.root),)


def test_qmlscene_paints_test_item(tmp_path, environment):
    file_path = tmp_path/'eeyore'
    environment[pyqtplugins.examples.exampleqmlitem.test_path_env_var] = fspath(file_path)

    qml_example_path = pyqtplugins.utilities.fspath(
        pathlib.Path(pyqtplugins.examples.__file__).parent / 'qmlapp.qml'
    )

    pyqtplugins.utilities.print_environment_variables(environment, *vars_to_print)

    with pytest.raises(subprocess.TimeoutExpired):
        subprocess.run(
            [
                fspath(qttools.application_path('qmlscene')),
                fspath(qml_example_path),
            ],
            check=True,
            env=environment,
            timeout=20,
        )

    assert (
            file_path.read_bytes()
            == pyqtplugins.examples.exampleqmlitem.test_file_contents
    )


def test_qmltestrunner_paints_test_item(tmp_path, environment):
    file_path = tmp_path/'piglet'
    environment[pyqtplugins.examples.exampleqmlitem.test_path_env_var] = fspath(file_path)

    qml_test_path = pyqtplugins.utilities.fspath(
        pathlib.Path(pyqtplugins.examples.__file__).parent / 'qmltest.qml'
    )

    pyqtplugins.utilities.print_environment_variables(environment, *vars_to_print)

    subprocess.run(
        [
            fspath(qttools.application_path('qmltestrunner')),
            '-input',
            qml_test_path,
        ],
        check=True,
        env=environment,
        timeout=20,
    )

    assert (
            file_path.read_bytes()
            == pyqtplugins.examples.exampleqmlitem.test_file_contents
    )
