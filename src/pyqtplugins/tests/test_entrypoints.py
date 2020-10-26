import os
import pathlib
import subprocess
import sys

import pytest
import qttools

import pyqtplugins.entrypoints
import pyqtplugins.examples.exampleqmlitem
import pyqtplugins.tests.testbutton
import pyqtplugins.tests.testbuttonplugin
import pyqtplugins.utilities


fspath = getattr(os, 'fspath', str)


vars_to_print = [
    'DISPLAY',
    'LD_LIBRARY_PATH'
    'PYQTDESIGNERPATH',
    'PYTHONPATH',
    'PATH',
    'QML2_IMPORT_PATH',
    'QT_DEBUG_PLUGINS',
    'QT_PLUGIN_PATH',
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
                [fspath(qttools.application_path('qmlscene'))],
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
            [fspath(qttools.application_path('qmltestrunner'))],
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


# @pytest.mark.skipif(sys.platform != 'linux', reason='only linux has ldd')
# def test_debug_ldd_qmlscene():
#     qmlscene = pyqtplugins.entrypoints.bin / 'qmlscene'
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
