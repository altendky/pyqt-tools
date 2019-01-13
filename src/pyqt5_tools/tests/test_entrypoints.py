import os
import pathlib
import subprocess
import sys

import pytest

import pyqt5_tools.tests.testbutton
import pyqt5_tools.tests.testbuttonplugin
import pyqt5_tools.examples.exampleqmlitem


fspath = getattr(os, 'fspath', str)


def test_designer_creates_test_widget(tmp_path):
    env = dict(os.environ)
    file_path = tmp_path/'tigger'
    env[pyqt5_tools.tests.testbutton.test_path_env_var] = fspath(file_path)

    widget_plugin_path = pathlib.Path(
        pyqt5_tools.tests.testbuttonplugin.__file__,
    ).parent

    with pytest.raises(subprocess.TimeoutExpired):
        subprocess.run(
            [
                fspath(
                    pathlib.Path(sys.executable).with_name('pyqt5designer'),
                ),
                '--widget-path', fspath(widget_plugin_path),
            ],
            check=True,
            env=env,
            timeout=10,
        )

    assert (
        file_path.read_bytes()
        == pyqt5_tools.tests.testbutton.test_file_contents
    )


def test_qmlscene_paints_test_item(tmp_path):
    env = dict(os.environ)
    file_path = tmp_path/'eeyore'
    env[pyqt5_tools.examples.exampleqmlitem.test_path_env_var] = fspath(file_path)

    with pytest.raises(subprocess.TimeoutExpired):
        subprocess.run(
            [
                fspath(
                    pathlib.Path(sys.executable).with_name('pyqt5qmlscene'),
                ),
                '--run-qml-example',
            ],
            check=True,
            env=env,
            timeout=10,
        )

    assert (
        file_path.read_bytes()
        == pyqt5_tools.examples.exampleqmlitem.test_file_contents
    )


def test_qmltestrunner_paints_test_item(tmp_path):
    env = dict(os.environ)
    file_path = tmp_path/'eeyore'
    env[pyqt5_tools.examples.exampleqmlitem.test_path_env_var] = fspath(file_path)

    subprocess.run(
        [
            fspath(
                pathlib.Path(sys.executable).with_name('pyqt5qmltestrunner'),
            ),
            '--test-qml-example',
        ],
        check=True,
        env=env,
        timeout=10,
    )

    assert (
        file_path.read_bytes()
        == pyqt5_tools.examples.exampleqmlitem.test_file_contents
    )
