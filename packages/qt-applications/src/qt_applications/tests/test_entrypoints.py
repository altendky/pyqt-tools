import importlib
import os
import subprocess
import sys
import sysconfig

import pkg_resources
import pytest

major = int(pkg_resources.get_distribution(__name__.partition(".")[0]).version.partition(".")[0])


m = {
    "pyqt_tools": "pyqt{major}_tools".format(major=major),
    "pyqt_plugins": "pyqt{major}_plugins".format(major=major),
    "qt_tools": "qt{major}_tools".format(major=major),
    "qt_applications": "qt{major}_applications".format(major=major),
}


def import_it(*segments):
    majored = [m[segments[0]], *segments[1:]]
    return importlib.import_module(".".join(majored))


qt_applications = import_it("qt_applications")


fspath = getattr(os, 'fspath', str)


def add_to_env_var_path_list(environment, name, before, after):
    return {
        name: os.pathsep.join((
            *before,
            environment.get(name, ''),
            *after
        ))
    }


def create_environment(reference):
    environment = dict(reference)

    if sys.platform in ['linux', 'darwin']:
        if sys.platform == 'linux':
            variable = 'LD_LIBRARY_PATH'
        else:
            variable = 'DYLD_LIBRARY_PATH'
        environment.update(add_to_env_var_path_list(
            environment=environment,
            name=variable,
            before=[''],
            after=[sysconfig.get_config_var('LIBDIR')],
        ))
    if sys.platform == 'win32':
        environment.update(add_to_env_var_path_list(
            environment=environment,
            name='PATH',
            before=[''],
            after=[sysconfig.get_path('scripts')],
        ))

    return environment


def test_designer():
    path = fspath(qt_applications._application_path('designer'))
    if path.endswith('.app'):
        cmd = ["open", path]

        subprocess.run(
            cmd,
            check=True,
            env={**create_environment(os.environ), 'QT_DEBUG_PLUGINS': '1'},
            timeout=10,
        )
    else:
        cmd = [path]

        with pytest.raises(subprocess.TimeoutExpired):

            subprocess.run(
                cmd,
                check=True,
                env={**create_environment(os.environ), 'QT_DEBUG_PLUGINS': '1'},
                timeout=10,
            )


def test_qmlscene():
    with pytest.raises(subprocess.TimeoutExpired):
        subprocess.run(
            [
                fspath(qt_applications._application_path('qmlscene')),
            ],
            check=True,
            env={**create_environment(os.environ), 'QT_DEBUG_PLUGINS': '1'},
            timeout=10,
        )

# TODO: hangs on GHA
# def test_language():
#     completed_process = subprocess.run(
#         [
#             fspath(qt_applications._application_path('qtdiag')),
#         ],
#         check=True,
#         env={**os.environ, 'LANGUAGE': 'de_DE'},
#         stdout=subprocess.PIPE,
#         timeout=30,
#     )
#
#     assert b'de_DE' in completed_process.stdout
