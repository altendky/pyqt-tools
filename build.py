#!/usr/bin/env python3

import argparse
import os
import shutil
import subprocess
import sys

from distutils.core import run_setup

# TODO: CAMPid 935481834121236136785436129254676532
def setup(path, script_args=['develop']):
    backup = os.getcwd()
    os.chdir(path)
    run_setup(os.path.join(path, 'setup.py'),
              script_args=script_args)
    os.chdir(backup)


def main():
    vc = 'VCINSTALLDIR'
    if vc not in os.environ:
        # TODO: explain how to set it via that .bat
        raise Exception('Environment variable {} must be set'.format(vc))

    designer_path = os.path.join('c:/', 'Qt', 'Qt5.7.0', '5.7', 'msvc2015', 'bin', 'designer.exe')
    designer_destination = os.path.join('PyQt5-tools', 'designer')
    try:
        os.makedirs(designer_destination)
    except FileExistsError:
        pass
    shutil.copy(designer_path, designer_destination)
    windeployqt_path = os.path.join('c:/', 'Qt', 'Qt5.7.0', '5.7', 'msvc2015', 'bin', 'windeployqt.exe'),
    print(designer_destination)
    windeployqt = subprocess.Popen(
        [
            windeployqt_path,
            # TODO: doesn't find it and supposedly just copies the installer...
            '--compiler-runtime',
            os.path.basename(designer_path)
        ],
        cwd=designer_destination
    )
    windeployqt.check_returncode()
    

    setup('.', script_args=['bdist_wheel'])


if __name__ == '__main__':
    sys.exit(main())
