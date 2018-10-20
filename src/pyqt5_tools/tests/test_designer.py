import os
import pathlib
import subprocess
import sys

import pytest

import pyqt5_tools.testbutton


def test_creates_test_widget(tempdir):
    env = dict(os.environ)
    path = pathlib.Path(tempdir)/'tigger'
    env[pyqt5_tools.testbutton.test_path_env_var] = path

    with pytest.raises(subprocess.TimeoutExpired):
        subprocess.run(
            [
                str(pathlib.Path(sys.executable).with_name('pyqt5designer')),
                '--widget-path', str(pathlib.Path(__file__).parent),
            ],
            check=True,
            env=env,
            timeout=30,
        )

    with open(path, 'rb') as f:
        assert f.read() == pyqt5_tools.testbutton.test_file_contents
