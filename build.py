#!/usr/bin/env python3

import argparse
import os
import shutil
import stat
import subprocess
import sys


def main():
    designer_path = os.path.join('c:/', 'Qt', 'Qt5.7.0', '5.7', 'msvc2015', 'bin', 'designer.exe')
    designer_destination = os.path.join('PyQt5-tools', 'designer')
    try:
        os.makedirs(designer_destination)
    except FileExistsError:
        pass
    shutil.copy(designer_path, designer_destination)
    designer_plugin_path = os.path.join('c:/', 'Users', 'IEUser', 'Desktop', 'sysroot', 'pyqt5-install', 'designer', 'pyqt5.dll')
    designer_plugin_destination = os.path.join(designer_destination, 'plugins', 'designer')
    os.makedirs(designer_plugin_destination)
    shutil.copy(designer_plugin_path, designer_plugin_destination)

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
    redist_destination = os.path.join(designer_destination, os.path.basename(redist_path))
    shutil.copyfile(redist_path, redist_destination)
    os.chmod(redist_destination, stat.S_IWRITE)


if __name__ == '__main__':
    sys.exit(main())
