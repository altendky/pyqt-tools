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
    os.makedirs(designer_destination, exist_ok=True)
    shutil.copy(designer_path, designer_destination)
    designer_plugin_path = os.path.join('c:/', 'Users', 'IEUser', 'Desktop', 'sysroot', 'pyqt5-install', 'designer', 'pyqt5.dll')
    designer_plugin_destination = os.path.join(designer_destination, 'plugins', 'designer')
    os.makedirs(designer_plugin_destination, exist_ok=True)
    shutil.copy(designer_plugin_path, designer_plugin_destination)
    python_dll_path = os.path.join('venv', 'Scripts', 'python35.dll')
    shutil.copy(python_dll_path, designer_destination)

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
        'redist', 'x86', 'Microsoft.VC140.CRT'
    )
    redist_files = [
        'msvcp140.dll',
        'vcruntime140.dll'
    ]
    for file in redist_files:
        dest = os.path.join(designer_destination, file)
        shutil.copyfile(os.path.join(redist_path, file), dest)
        os.chmod(dest, stat.S_IWRITE)


if __name__ == '__main__':
    sys.exit(main())
