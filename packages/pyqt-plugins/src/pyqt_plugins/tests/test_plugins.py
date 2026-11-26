import os
import pathlib
import subprocess
import time
import sys

import pytest

# TODO: CAMPid 0970432108721340872130742130870874321
import importlib
import pkg_resources

string_version = pkg_resources.get_distribution(__name__.partition('.')[0]).version
version = tuple(
    int(segment)
    for segment in string_version.split('.')[:3]
)
major = version[0]


def import_it(*segments):
    m = {
        "pyqt_tools": "pyqt{major}_tools".format(major=major),
        "pyqt_plugins": "pyqt{major}_plugins".format(major=major),
        "qt_tools": "qt{major}_tools".format(major=major),
        "qt_applications": "qt{major}_applications".format(major=major),
        "PyQt": "PyQt{major}".format(major=major),
    }

    majored = [m[segments[0]], *segments[1:]]
    return importlib.import_module(".".join(majored))


qt_tools = import_it("qt_tools")
pyqt_plugins = import_it("pyqt_plugins")
import_it("pyqt_plugins", "examples", "exampleqmlitem")
import_it("pyqt_plugins", "tests", "testbutton")
import_it("pyqt_plugins", "tests", "testbuttonplugin")
import_it("pyqt_plugins", "utilities")


fspath = getattr(os, 'fspath', str)


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


def run_for_file(
        *args,
        file_path,
        file_exists_timeout=60,
        file_write_time_allowance=5,
        **kwargs
):
    print('Launching: {}'.format(args[0]))
    process = subprocess.Popen(*args, **kwargs)

    deadline = time.monotonic() + file_exists_timeout

    while True:
        time.sleep(1)

        if process.poll() is not None:
            raise Exception('process ended with return code: {}'.format(process.returncode))

        if file_path.exists():
            break

        if time.monotonic() > deadline:
            raise Exception(
                'file not written within {} seconds'.format(file_exists_timeout),
            )

    time.sleep(file_write_time_allowance)

    return file_path.read_bytes()


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

    command_elements = qt_tools.create_command_elements(
        name='designer',
        sys_platform=sys.platform,
    )

    contents = run_for_file(
        command_elements,
        env=environment,
        file_path=file_path,
    )

    assert contents == pyqt_plugins.tests.testbutton.test_file_contents


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

    command_elements = qt_tools.create_command_elements(
        name='qmlscene',
        sys_platform=sys.platform,
    )

    contents = run_for_file(
        [
            *command_elements,
            fspath(qml_example_path),
        ],
        env=environment,
        file_path=file_path,
    )

    assert contents == pyqt_plugins.examples.exampleqmlitem.test_file_contents


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

    command_elements = qt_tools.create_command_elements(
        name='qmltestrunner',
        sys_platform=sys.platform,
    )

    subprocess.run(
        [
            *command_elements,
            '-input',
            qml_test_path,
        ],
        check=True,
        env=environment,
        timeout=60,
    )

    assert (
            file_path.read_bytes()
            == pyqt_plugins.examples.exampleqmlitem.test_file_contents
    )
