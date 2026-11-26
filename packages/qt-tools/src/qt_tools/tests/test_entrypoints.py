import os
import pathlib
import subprocess
import sys
import sysconfig

import pytest


fspath = getattr(os, 'fspath', str)

scripts_path = pathlib.Path(sysconfig.get_path('scripts'))


# TODO: CAMPid 0970432108721340872130742130870874321
import importlib
import pkg_resources

major = int(pkg_resources.get_distribution(__name__.partition('.')[0]).version.partition(".")[0])


def import_it(*segments):

    m = {
        "pyqt_tools": "pyqt{major}_tools".format(major=major),
        "pyqt_plugins": "pyqt{major}_plugins".format(major=major),
        "qt_tools": "qt{major}_tools".format(major=major),
        "qt_applications": "qt{major}_applications".format(major=major),
    }

    majored = [m[segments[0]], *segments[1:]]
    return importlib.import_module(".".join(majored))


qt_tools = import_it("qt_tools")


def test_designer():
    environment = qt_tools.create_environment()

    with pytest.raises(subprocess.TimeoutExpired):
        subprocess.run(
            [
                fspath(scripts_path.joinpath('qt{}-tools'.format(major))),
                'designer',
            ],
            check=True,
            env={**environment, 'QT_DEBUG_PLUGINS': '1'},
            timeout=10,
        )


def test_qmlscene():
    environment = qt_tools.create_environment()

    with pytest.raises(subprocess.TimeoutExpired):
        subprocess.run(
            [
                fspath(scripts_path.joinpath('qt{}-tools'.format(major))),
                'qmlscene',
            ],
            check=True,
            env={**environment, 'QT_DEBUG_PLUGINS': '1'},
            timeout=10,
        )

# TODO: hangs on GHA
# def test_language():
#     completed_process = subprocess.run(
#         [
#             fspath(scripts_path.joinpath('qt5-tools')),
#             'qtdiag',
#         ],
#         check=True,
#         env={**os.environ, 'LANGUAGE': 'de_DE'},
#         stdout=subprocess.PIPE,
#         timeout=30,
#     )
#
#     assert b'de_DE' in completed_process.stdout
