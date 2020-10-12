import os
import pathlib
import subprocess
import sys

import pytest


fspath = getattr(os, 'fspath', str)


def test_designer_creates_test_widget():
    with pytest.raises(subprocess.TimeoutExpired):
        subprocess.run(
            [
                fspath(
                    pathlib.Path(sys.executable).with_name('pyqt5designer'),
                ),
                '--qt-debug-plugins',
            ],
            check=True,
            timeout=10,
        )


def test_qmlscene_paints_test_item():
    with pytest.raises(subprocess.TimeoutExpired):
        subprocess.run(
            [
                fspath(
                    pathlib.Path(sys.executable).with_name('pyqt5qmlscene'),
                ),
                '--qt-debug-plugins',
            ],
            check=True,
            timeout=10,
        )


def test_qmltestrunner_paints_test_item():
    subprocess.run(
        [
            fspath(
                pathlib.Path(sys.executable).with_name('pyqt5qmltestrunner'),
            ),
            '--qt-debug-plugins',
        ],
        check=True,
        timeout=10,
    )
