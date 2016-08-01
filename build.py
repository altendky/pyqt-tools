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
    designer_path = os.path.join('c:/', 'Qt', 'Qt5.7.0', '5.7', 'msvc2015', 'bin', 'designer.exe')
    designer_destination = os.path.join('PyQt5-tools', 'designer')
    try:
        os.makedirs(designer_destination)
    except FileExistsError:
        pass
    shutil.copy(designer_path, designer_destination)

    windeployqt_path = os.path.join('c:/', 'Qt', 'Qt5.7.0', '5.7', 'msvc2015', 'bin', 'windeployqt.exe'),
    windeployqt = subprocess.Popen(
        [
            windeployqt_path,
            os.path.basename(designer_path)
        ],
        cwd=designer_destination
    )
    windeployqt.wait(timeout=15)
    if windeployqt.returncode != 0:
        raise Exception('windeployqt failed with return code {}'
                        .format(winqtdeploy.returncode))

    # Since windeployqt doesn't actually work with --compiler-runtime,
    # copy it ourselves
    redist_path = os.path.join(
        'c:/', 'Program Files (x86)', 'Microsoft Visual Studio 14.0', 'VC',
        'redist', 'x86', 'Microsoft.VC140.CRT', 'msvcp140.dll'
    )
    shutil.copyfile(
        redist_path,
        os.path.join(designer_destination, os.path.basename(redist_path))
    )

    setup('.', script_args=['bdist_wheel'])


if __name__ == '__main__':
    sys.exit(main())
