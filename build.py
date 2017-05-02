#!/usr/bin/env python3

import argparse
import io
import os
import platform
import urllib.request
import shutil
import stat
import subprocess
import sys
import zipfile

import requests


# http://stackoverflow.com/a/9728478/228539
def list_files(startpath):
    for root, dirs, files in os.walk(startpath):
        level = root.replace(startpath, '').count(os.sep)
        indent = ' ' * 4 * (level)
        print('{}{}/'.format(indent, os.path.basename(root)))
        subindent = ' ' * 4 * (level + 1)
        for f in files:
            print('{}{}'.format(subindent, f))


def main():
    bits = int(platform.architecture()[0][0:2])
    print(bits)
    if bits == 32:
        compiler_dir = 'msvc2015'
    elif bits == 64:
        compiler_dir = 'msvc2015_64'

    qt_bin_path = os.path.join('c:/', 'Qt', '5.8', compiler_dir, 'bin')

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

    applications = []
    # for file in os.listdir(qt_bin_path):
    #     base, ext = os.path.splitext(file)
    #     if ext == '.exe':
    #         applications.append(file)

    destination = 'pyqt5-tools'
    os.makedirs(destination, exist_ok=True)

    windeployqt_path = os.path.join(qt_bin_path, 'windeployqt.exe'),

    for file in applications:
        print("\n\n   - - -   Copying {} and it's dependencies".format(file))
        file_path = os.path.join(qt_bin_path, file)
        shutil.copy(file_path, destination)

        windeployqt = subprocess.Popen(
            [
                windeployqt_path,
                os.path.basename(file_path)
            ],
            cwd=destination
        )
        windeployqt.wait(timeout=15)
        if windeployqt.returncode != 0:
            print('\n\nwindeployqt failed with return code {}\n\n'
                            .format(windeployqt.returncode))

    # application_paths = [
        # 'assistant.exe',
        # 'designer.exe',
        # 'linguist.exe'
    # ]


    # for application in application_paths:
        # application_path = os.path.join(qt_bin_path, application)
        # os.makedirs(destination, exist_ok=True)
        # shutil.copy(application_path, destination)

        # windeployqt = subprocess.Popen(
            # [
                # windeployqt_path,
                # os.path.basename(application)
            # ],
            # cwd=destination
        # )
        # windeployqt.wait(timeout=15)
        # if windeployqt.returncode != 0:
            # raise Exception('windeployqt failed with return code {}'
                            # .format(winqtdeploy.returncode))

    build = os.environ['APPVEYOR_BUILD_FOLDER']
    sysroot = os.path.join(build, 'sysroot')
    os.makedirs(sysroot)
    os.environ['SYSROOT'] = sysroot
    r = requests.get('http://downloads.sourceforge.net/project/pyqt/sip/sip-4.19.2/sip-4.19.2.zip')
    r = requests.get('http://downloads.sourceforge.net/project/pyqt/PyQt5/PyQt-5.8.2/PyQt5_gpl-5.8.2.zip')
    z = zipfile.ZipFile(io.BytesIO(r.content))
    src = os.path.join(build, 'src')
    os.makedirs(src)
    z.extractall(path=os.path.join(src))
    print('<{}>'.format(build))
    venv_bin = os.path.join(build, 'venv', 'Scripts')
    pyqt5 = os.path.join(src, 'PyQt5_gpl-5.8.2')
    subprocess.check_call(
        [
            os.path.join(venv_bin, 'pyqtdeploycli'),
            '--package', 'pyqt5',
            '--target', 'win-32',
            'configure',
        ],
        cwd=pyqt5,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    pyqt5_cfg = os.path.join(pyqt5, 'pyqt5-win.cfg')
    with open(pyqt5_cfg) as f:
        original = io.StringIO(f.read())
    with open(pyqt5_cfg, 'w') as f:
        for line in original:
            if line.startswith('py_pylib_lib'):
                f.write('py_pylib_lib = python%(py_major)%(py_minor)\n')
            else:
                f.write(line)
        f.write('\npy_pyshlib = python36.dll\n')
    designer_pro = os.path.join(pyqt5, 'designer', 'designer.pro-in')
    with open(designer_pro, 'a') as f:
        f.write('\nDEFINES     += PYTHON_LIB=\'"\\\\\\"@PYSHLIB@\\\\\\""\'\n')
    qmake = os.path.join(qt_bin_path, 'qmake.exe')
    subprocess.check_call(
        [
            sys.executable,
            'configure.py',
            '--static',
            '--sysroot="%SYSROOT%"',
            '--no-tools',
            '--no-qsci-api',
            '--no-qml-plugin',
            '--configuration=pyqt5-win.cfg',
            '--qmake="{}"'.format(qmake),
            '--confirm-license',
            '--sip="%SYSROOT%\native\sip.exe"',
            '--bindir="%SYSROOT%\pyqt5-install\bin"',
            '--destdir="%SYSROOT%\pyqt5-install\dest"',
            '--designer-plugindir="%SYSROOT%\pyqt5-install\designer" --enable=QtDesigner',
        ],
        cwd=pyqt5,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    subprocess.check_call(
        [
            qmake
        ],
        cwd=pyqt5,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    subprocess.check_call(
        [
            'nmake'
        ],
        cwd=pyqt5,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    subprocess.check_call(
        [
            'nmake install'
        ],
        cwd=pyqt5,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    designer_plugin_path = os.path.join(sysroot, 'pyqt5-install', 'designer', 'pyqt5.dll')
    designer_plugin_path = os.path.expandvars(designer_plugin_path)
    designer_plugin_destination = os.path.join(destination, 'plugins', 'designer')
    os.makedirs(designer_plugin_destination, exist_ok=True)
    shutil.copy(designer_plugin_path, designer_plugin_destination)
    shutil.copy(os.path.join('..', 'PyQt5_gpl-5.7-designer', 'LICENSE'),
                os.path.join('pyqt5-tools', 'LICENSE.pyqt5'))

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
        dest = os.path.join(destination, file)
        shutil.copyfile(os.path.join(redist_path, file), dest)
        os.chmod(dest, stat.S_IWRITE)

    redist_license = os.path.join('pyqt5-tools', 'REDIST.visual_cpp_build_tools')
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
