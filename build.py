#!/usr/bin/env python3

import glob
import io
import itertools
import os
import platform
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


def validate_pair(ob):
    try:
        if not (len(ob) == 2):
            print("Unexpected result:", ob, file=sys.stderr)
            raise ValueError
    except:
        return False
    return True


def consume(iter):
    try:
        while True: next(iter)
    except StopIteration:
        pass


def get_environment_from_batch_command(env_cmd, initial=None):
    """
    Take a command (either a single command or list of arguments)
    and return the environment created after running that command.
    Note that if the command must be a batch file or .cmd file, or the
    changes to the environment will not be captured.

    If initial is supplied, it is used as the initial environment passed
    to the child process.
    """
    if not isinstance(env_cmd, (list, tuple)):
        env_cmd = [env_cmd]
    # construct the command that will alter the environment
    env_cmd = subprocess.list2cmdline(env_cmd)
    # create a tag so we can tell in the output when the proc is done
    tag = bytes('Done running command', 'UTF-8')
    # construct a cmd.exe command to do accomplish this
    cmd = 'cmd.exe /s /c "{env_cmd} && echo "{tag}" && set"'.format(**vars())
    # launch the process
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, env=initial)
    # parse the output sent to stdout
    lines = proc.stdout
    # consume whatever output occurs until the tag is reached
    consume(itertools.takewhile(lambda l: tag not in l, lines))
    # define a way to handle each KEY=VALUE line
    handle_line = lambda l: str(l, 'UTF-8').rstrip().split('=',1)
    # parse key/values into pairs
    pairs = map(handle_line, lines)
    # make sure the pairs are valid
    valid_pairs = filter(validate_pair, pairs)
    # construct a dictionary of the pairs
    result = dict(valid_pairs)
    # let the process finish
    proc.communicate()
    return result


def main():
    bits = int(platform.architecture()[0][0:2])
    python_major_minor = os.environ['PYTHON'][-2:]
    msvc_versions = {'34': 10, '35': 14, '36': 14}
    msvc_version = msvc_versions[python_major_minor]
    vs_path = os.path.join(
        'C:/', 'Program Files (x86)', 'Microsoft Visual Studio {}.0'.format(
            msvc_version
        )
    )

    os.environ = get_environment_from_batch_command(
        [
            os.path.join(vs_path, 'VC', 'vcvarsall.bat'),
            {32: 'x86', 64: 'x64'}[bits]
        ],
        initial=os.environ
    )

    compiler_dir = {32: 'msvc{}', 64: 'msvc{}_64'}[bits]
    compiler_dir = compiler_dir.format(
        {'34': 2010, '35': 2015, '36': 2015}[python_major_minor])

    qt_bin_path = os.path.join(os.environ['QT_BASE_PATH'], compiler_dir, 'bin')

    with open('setup.cfg', 'w') as cfg:
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

    build = os.environ['APPVEYOR_BUILD_FOLDER']

    destination = os.path.join(build, 'pyqt5-tools')
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

    application_paths = glob.glob(os.path.join(qt_bin_path, '*.exe'))

    os.makedirs(destination, exist_ok=True)

    for application in application_paths:
        application_path = os.path.join(qt_bin_path, application)

        shutil.copy(application_path, destination)

        p = subprocess.run(
            [
                windeployqt_path,
                os.path.basename(application),
                '--dry-run',
                '--list', 'source',
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if p.returncode != 0 or b'Qt5WebEngineCore' in p.stdout:
           continue

        windeployqt = subprocess.Popen(
            [
                windeployqt_path,
                os.path.basename(application)
            ],
            cwd=destination
        )
        windeployqt.wait(timeout=15)
        if windeployqt.returncode != 0:
            raise Exception('windeployqt failed with return code {}'
                            .format(windeployqt.returncode))

    sysroot = os.path.join(build, 'sysroot')
    os.makedirs(sysroot)
    nmake = os.path.join(vs_path, 'VC', 'BIN', 'nmake'),
    qmake = os.path.join(qt_bin_path, 'qmake.exe')
    print('qmake: {}'.format(qmake))

    src = os.path.join(build, 'src')
    os.makedirs(src)
    venv_bin = os.path.join(build, 'venv', 'Scripts')
    native = os.path.join(sysroot, 'native')
    os.makedirs(native)

    subprocess.check_call(
        [
            os.path.join(venv_bin, 'pyqtdeploycli'),
            '--sysroot', sysroot,
            '--package', 'python',
            '--system-python', '3.6',
            'install',
        ],
    )

    r = requests.get('http://downloads.sourceforge.net/project/pyqt/sip/sip-4.19.2/sip-4.19.2.zip')
    z = zipfile.ZipFile(io.BytesIO(r.content))
    z.extractall(path=src)
    sip = os.path.join(src, 'sip-4.19.2')
    native_sip = sip + '-native'
    shutil.copytree(os.path.join(src, 'sip-4.19.2'), native_sip)
    os.environ['CL'] = '/I"{}\\include\\python3.6"'.format(sysroot)
    subprocess.check_call(
        [
            sys.executable,
            'configure.py',
            '--static',
            '--sysroot={}'.format(native),
        ],
        cwd=native_sip,
    )
    subprocess.check_call(
        [
           nmake,
        ],
        cwd=native_sip,
        env=os.environ,
    )
    subprocess.check_call(
        [
            nmake,
            'install',
        ],
        cwd=native_sip,
        env=os.environ,
    )

    subprocess.check_call(
        [
            os.path.join(venv_bin, 'pyqtdeploycli'),
            '--package', 'sip',
            '--target', 'win-{}'.format(bits),
            'configure',
        ],
        cwd=sip,
    )
    subprocess.check_call(
        [
            sys.executable,
            'configure.py',
            '--static',
            '--sysroot={}'.format(sysroot),
            '--no-tools',
            '--use-qmake',
            '--configuration=sip-win.cfg'
        ],
        cwd=sip,
    )
    subprocess.check_call(
        [
            qmake
        ],
        cwd=sip,
    )
    subprocess.check_call(
        [
            nmake,
        ],
        cwd=sip,
        env=os.environ,
    )
    subprocess.check_call(
        [
            nmake,
            'install',
        ],
        cwd=sip,
        env=os.environ,
    )

    r = requests.get('http://downloads.sourceforge.net/project/pyqt/PyQt5/PyQt-5.8.2/PyQt5_gpl-5.8.2.zip')
    z = zipfile.ZipFile(io.BytesIO(r.content))
    z.extractall(path=src)
    pyqt5 = os.path.join(src, 'PyQt5_gpl-5.8.2')
    subprocess.check_call(
        [
            os.path.join(venv_bin, 'pyqtdeploycli'),
            '--package', 'pyqt5',
            '--target', 'win-{}'.format(bits),
            'configure',
        ],
        cwd=pyqt5,
    )
    pyqt5_cfg = os.path.join(pyqt5, 'pyqt5-win.cfg')
    with open(pyqt5_cfg) as f:
        original = io.StringIO(f.read())
    with open(pyqt5_cfg, 'w') as f:
        f.write('\npy_pyshlib = python{}.dll\n'.format(
            os.environ['PYTHON'][-2:],
        ))
        for line in original:
            if line.startswith('py_pylib_lib'):
                f.write('py_pylib_lib = python%(py_major)%(py_minor)\n')
            else:
                f.write(line)
    designer_pro = os.path.join(pyqt5, 'designer', 'designer.pro-in')
    with open(designer_pro, 'a') as f:
        f.write('\nDEFINES     += PYTHON_LIB=\'"\\\\\\"@PYSHLIB@\\\\\\""\'\n')
    subprocess.check_call(
        [
            sys.executable,
            r'configure.py',
            r'--static',
            r'--sysroot={}'.format(sysroot),
            r'--no-tools',
            r'--no-qsci-api',
            r'--no-qml-plugin',
            r'--configuration={}'.format(pyqt5_cfg),
            r'--qmake={}'.format(qmake),
            r'--confirm-license',
            r'--sip={}\sip.exe'.format(native),
            r'--bindir={}\pyqt5-install\bin'.format(sysroot),
            r'--destdir={}\pyqt5-install\dest'.format(sysroot),
            r'--designer-plugindir={}\pyqt5-install\designer'.format(sysroot),
            r'--enable=QtDesigner',
        ],
        cwd=pyqt5,
    )
    subprocess.check_call(
        [
            qmake
        ],
        cwd=pyqt5,
    )
    subprocess.check_call(
        [
            nmake,
        ],
        cwd=pyqt5,
        env=os.environ,
    )
    subprocess.check_call(
        [
            nmake,
            'install',
        ],
        cwd=pyqt5,
        env=os.environ,
    )
    designer_plugin_path = os.path.join(sysroot, 'pyqt5-install', 'designer', 'pyqt5.dll')
    designer_plugin_path = os.path.expandvars(designer_plugin_path)
    designer_plugin_destination = os.path.join(destination, 'plugins', 'designer')
    os.makedirs(designer_plugin_destination, exist_ok=True)
    shutil.copy(designer_plugin_path, designer_plugin_destination)
    shutil.copy(os.path.join(pyqt5, 'LICENSE'),
                os.path.join(destination, 'LICENSE.pyqt5'))

    # Since windeployqt doesn't actually work with --compiler-runtime,
    # copy it ourselves
    plat = {32: 'x86', 64: 'x64'}[bits]
    redist_path = os.path.join(
        vs_path, 'VC', 'redist', plat, 'Microsoft.VC{}0.CRT'.format(msvc_version)
    )
    redist_files = [
        'msvcp{}0.dll'.format(msvc_version),
        'vcruntime{}0.dll'.format(msvc_version),
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

    r = requests.get('https://www.visualstudio.com/DownloadEula/en-us/mt644918')
    c = io.StringIO(r.text)
    with open(redist_license_html, 'w') as f:
        f.write(c.read())


if __name__ == '__main__':
    sys.exit(main())
