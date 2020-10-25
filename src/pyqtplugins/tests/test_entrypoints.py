import os
import pathlib
import subprocess
import sys

import pytest

import pyqtplugins.entrypoints
import pyqtplugins.examples.exampleqmlitem
import pyqtplugins.tests.testbutton
import pyqtplugins.tests.testbuttonplugin
import pyqtplugins.utilities


fspath = getattr(os, 'fspath', str)


def test_designer_creates_test_widget(tmp_path):
    env = pyqtplugins.utilities.create_env(os.environ)
    env['QT_DEBUG_PLUGINS'] = '1'

    file_path = tmp_path/'tigger'
    env[pyqtplugins.tests.testbutton.test_path_env_var] = fspath(file_path)

    widget_plugin_path = pathlib.Path(
        pyqtplugins.tests.testbuttonplugin.__file__,
    ).parent

    env.update(pyqtplugins.utilities.add_to_env_var_path_list(
        env=env,
        name='PYQTDESIGNERPATH',
        before=[fspath(widget_plugin_path)],
        after=[''],
    ))

    vars_to_print = [
        'PYQTDESIGNERPATH',
        'PYTHONPATH',
        'PATH',
        'QT_DEBUG_PLUGINS',
        'QT_PLUGIN_PATH',
        pyqtplugins.tests.testbutton.test_path_env_var,
    ]

    if sys.platform == 'linux':
        vars_to_print.append('LD_LIBRARY_PATH')
        vars_to_print.append('DISPLAY')

    pyqtplugins.utilities.print_environment_variables(env, *vars_to_print)

    with pytest.raises(subprocess.TimeoutExpired):
        subprocess.run(
            [
                fspath(
                    pathlib.Path(sys.executable).with_name('designer'),
                ),
            ],
            check=True,
            env=env,
            timeout=20,
        )

    assert (
            file_path.read_bytes()
            == pyqtplugins.tests.testbutton.test_file_contents
    )


qml2_import_paths = (pyqtplugins.utilities.fspath(pyqtplugins.root),)


def test_qmlscene_paints_test_item(tmp_path):
    env = pyqtplugins.utilities.create_env(os.environ)

    pyqtplugins.utilities.mutate_qml_path(env, paths=qml2_import_paths)
    env['QT_DEBUG_PLUGINS'] = '1'

    file_path = tmp_path/'eeyore'
    env[pyqtplugins.examples.exampleqmlitem.test_path_env_var] = fspath(file_path)

    qml_example_path = pyqtplugins.utilities.fspath(
        pathlib.Path(pyqtplugins.examples.__file__).parent / 'qmlapp.qml'
    )

    vars_to_print = [
        'QML2_IMPORT_PATH',
        'PYTHONPATH',
        'PATH',
        'QT_DEBUG_PLUGINS',
        'QT_PLUGIN_PATH',
        pyqtplugins.examples.exampleqmlitem.test_path_env_var,
    ]

    if sys.platform == 'linux':
        vars_to_print.append('LD_LIBRARY_PATH')
        vars_to_print.append('DISPLAY')

    pyqtplugins.utilities.print_environment_variables(env, *vars_to_print)

    with pytest.raises(subprocess.TimeoutExpired):
        subprocess.run(
            [
                fspath(
                    pathlib.Path(sys.executable).with_name('qmlscene'),
                ),
                fspath(qml_example_path),
            ],
            check=True,
            env=env,
            timeout=20,
        )

    assert (
            file_path.read_bytes()
            == pyqtplugins.examples.exampleqmlitem.test_file_contents
    )


def test_qmltestrunner_paints_test_item(tmp_path):
    env = pyqtplugins.utilities.create_env(os.environ)

    pyqtplugins.utilities.mutate_qml_path(env, paths=qml2_import_paths)
    env['QT_DEBUG_PLUGINS'] = '1'

    file_path = tmp_path/'piglet'
    env[pyqtplugins.examples.exampleqmlitem.test_path_env_var] = fspath(file_path)

    qml_test_path = pyqtplugins.utilities.fspath(
        pathlib.Path(pyqtplugins.examples.__file__).parent / 'qmltest.qml'
    )

    vars_to_print = [
        'QML2_IMPORT_PATH',
        'PYTHONPATH',
        'PATH',
        'QT_DEBUG_PLUGINS',
        'QT_PLUGIN_PATH',
        pyqtplugins.examples.exampleqmlitem.test_path_env_var,
    ]

    if sys.platform == 'linux':
        vars_to_print.append('LD_LIBRARY_PATH')
        vars_to_print.append('DISPLAY')

    pyqtplugins.utilities.print_environment_variables(env, *vars_to_print)

    subprocess.run(
        [
            fspath(
                pathlib.Path(sys.executable).with_name('qmltestrunner'),
            ),
            '-input',
            qml_test_path,
        ],
        check=True,
        env=env,
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
