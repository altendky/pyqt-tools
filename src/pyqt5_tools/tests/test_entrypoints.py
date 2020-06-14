import os
import pathlib
import subprocess
import sys

import pytest

import pyqt5_tools.entrypoints
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
                '--qt-debug-plugins',
            ],
            check=True,
            env=env,
            timeout=90,
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
                '--qt-debug-plugins',
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
    file_path = tmp_path/'piglet'
    env[pyqt5_tools.examples.exampleqmlitem.test_path_env_var] = fspath(file_path)

    subprocess.run(
        [
            fspath(
                pathlib.Path(sys.executable).with_name('pyqt5qmltestrunner'),
            ),
            '--test-qml-example',
            '--qt-debug-plugins',
        ],
        check=True,
        env=env,
        timeout=10,
    )

    assert (
        file_path.read_bytes()
        == pyqt5_tools.examples.exampleqmlitem.test_file_contents
    )


# @pytest.mark.skipif(sys.platform != 'linux', reason='only linux has ldd')
# def test_debug_ldd_qmlscene():
#     qmlscene = pyqt5_tools.entrypoints.bin / 'qmlscene'
#
#     subprocess.run(['ldd', qmlscene], check=True)
#
#
# def test_debug_pip_freeze():
#     subprocess.run(
#         [
#             sys.executable,
#             '-m', 'pip',
#             'freeze',
#         ],
#         check=True,
#     )
#
#
# def test_debug_pyqt5_sip_path():
#     subprocess.run(
#         [
#             sys.executable,
#             '-c',
#             'import PyQt5.sip; print(PyQt5.sip)',
#         ],
#         check=True,
#     )
#
#
# def test_debug_cwd():
#     print('cwd:', pathlib.Path.cwd())
#
#
# def test_debug_directory_contents():
#     cwd = pathlib.Path.cwd()
#     for path in cwd.iterdir():
#         print('     {} {}'.format(
#             'd' if path.is_dir() else 'f',
#             path.relative_to(cwd),
#         ))
#
#
# def test_debug_sys_path_contents():
#     files = set()
#     directories = set()
#
#     for string_path in sys.path:
#         maybe_directory = pathlib.Path(string_path)
#         if maybe_directory.is_dir():
#             directory = maybe_directory
#             for path in directory.iterdir():
#                 if path.is_dir():
#                     directories.add(path)
#                 elif path.suffix == '.py' and path.is_file():
#                     files.add(path)
#
#     for paths in [files, directories]:
#         for path in sorted(paths):
#             print('     {} {}'.format(
#                 'd' if path.is_dir() else 'f',
#                 path.resolve(),
#             ))
