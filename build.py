#!/usr/bin/env python3

import argparse
import os
import platform
import urllib.request
import shutil
import stat
import subprocess
import sys


def main():
    bits = int(platform.architecture()[0][0:2])
    print(bits)
    if bits == 32:
        compiler_dir = 'msvc2015'
    elif bits == 64:
        compiler_dir = 'msvc2015_64'

    qt_bin_path = os.path.join('c:/', 'Qt', 'Qt5.7.0', '5.7', compiler_dir, 'bin')

    with open('setup.cfg', 'w') as cfg:
        arch = platform.architecture()
        # TODO: CAMPid 994391911172312371845393249991437
        bits = int(arch[0][0:2])
        plat_names = {
            32: 'win32',
            64: 'win_amd64'
        }
        try:
            plat_name = plat_names[bits]
        except KeyError:
            raise Exception('Bit depth {bits} not recognized {}'.format(plat_names.keys()))

        python_tag = 'cp{major}{minor}'.format(
            major=sys.version_info[0],
            minor=sys.version_info[1],
        )

        cfg.write(
'''[bdist_wheel]
python-tag = {python_tag}
plat-name = {plat_name}'''.format(**locals()))

    designer_path = os.path.join(qt_bin_path, 'designer.exe')
    designer_destination = os.path.join('PyQt5-tools', 'designer')
    os.makedirs(designer_destination, exist_ok=True)
    shutil.copy(designer_path, designer_destination)
    designer_plugin_path = os.path.join('${SYSROOT}', 'pyqt5-install', 'designer', 'pyqt5.dll')
    designer_plugin_path = os.path.expandvars(designer_plugin_path)
    designer_plugin_destination = os.path.join(designer_destination, 'plugins', 'designer')
    os.makedirs(designer_plugin_destination, exist_ok=True)
    shutil.copy(designer_plugin_path, designer_plugin_destination)
    shutil.copy(os.path.join('..', 'PyQt5_gpl-5.7-designer', 'LICENSE'),
                os.path.join('PyQt5-tools', 'LICENSE.pyqt5'))

    python_dll_path = os.path.join('venv', 'Scripts', 'python35.dll')
    shutil.copy(python_dll_path, designer_destination)

    windeployqt_path = os.path.join(qt_bin_path, 'windeployqt.exe'),
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
    plat = {32: 'x86', 64: 'x64'}[bits]
    redist_path = os.path.join(
        'c:/', 'Program Files (x86)', 'Microsoft Visual Studio 14.0', 'VC',
        'redist', plat, 'Microsoft.VC140.CRT'
    )
    redist_files = [
        'msvcp140.dll',
        'vcruntime140.dll'
    ]
    for file in redist_files:
        dest = os.path.join(designer_destination, file)
        shutil.copyfile(os.path.join(redist_path, file), dest)
        os.chmod(dest, stat.S_IWRITE)

    redist_license = os.path.join('PyQt5-tools', 'REDIST.visual_cpp_build_tools')
    redist_license_html = redist_license + '.html'
    with open(redist_license, 'w') as redist:
        redist.write(
'''The following filings are being distributed under the Microsoft Visual C++ Build Tools license linked below.

{files}

https://www.visualstudio.com/en-us/support/legal/mt644918


For a local copy see:

{license_file}
'''.format(files='\n'.join(redist_files),
           license_file=os.path.basename(redist_license_html)))

    urllib.request.urlretrieve(url='https://www.visualstudio.com/DownloadEula/en-us/mt644918',
                               filename=redist_license_html)


if __name__ == '__main__':
    sys.exit(main())
