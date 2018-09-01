#!/usr/bin/env python3

import decimal
import glob
import inspect
import io
import itertools
import os
import pathlib
import pip
import platform
import shlex
import shutil
import stat
import subprocess
import sys
import textwrap
import zipfile

import requests


class Results:
    def __init__(self, console_scripts):
        self.console_scripts = console_scripts


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
    tag = 'Done running command'
    # construct a cmd.exe command to do accomplish this
    cmd = 'cmd.exe /s /c "{env_cmd} && echo "{tag}" && set"'.format(**vars())
    # launch the process
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, env=initial, check=True)
    # parse the output sent to stdout
    lines = proc.stdout.decode().splitlines()
    # consume whatever output occurs until the tag is reached
    consume(itertools.takewhile(lambda l: tag not in l, lines))
    # define a way to handle each KEY=VALUE line
    handle_line = lambda l: l.rstrip().split('=',1)
    # parse key/values into pairs
    pairs = map(handle_line, lines)
    # make sure the pairs are valid
    valid_pairs = filter(validate_pair, pairs)
    # construct a dictionary of the pairs
    result = dict(valid_pairs)
    return result


# TODO: CAMPid 079079043724533410718467080456813604134316946765431341384014
def report_and_check_call(command, *args, cwd=None, shell=False, **kwargs):
    print('\nCalling:')
    print('    Caller: {}'.format(callers_line_info()))
    print('    CWD: {}'.format(repr(cwd)))
    print('    As passed: {}'.format(repr(command)))
    print('    Full: {}'.format(
        ' '.join(shlex.quote(getattr(os, 'fspath', str)(x)) for x in command),
    ))

    if shell:
        print('    {}'.format(repr(command)))
    else:
        for arg in command:
            print('    {}'.format(repr(arg)))

    sys.stdout.flush()
    return subprocess.run(command, *args, cwd=cwd, check=True, **kwargs)


# TODO: CAMPid 974597249731467124675t40136706803641679349342342
# https://github.com/altendky/altendpy/issues/8
def callers_line_info():
    here = inspect.currentframe()
    caller = here.f_back

    if caller is None:
        return None

    there = caller.f_back
    info = inspect.getframeinfo(there)

    return 'File "{}", line {}, in {}'.format(
        info.filename,
        info.lineno,
        info.function,
    )


def main():
    bits = int(platform.architecture()[0][0:2])
    python_major_minor = '{}{}'.format(
        sys.version_info.major,
        sys.version_info.minor
    )
    # WARNING: The compiler for Python 3.4 is actually 10 but let's try 12
    #          because that's what Qt offers
    msvc_versions = {
        '34': '12.0',
        '35': '14.0',
        '36': '14.0',
        '37': '14.14',
    }
    msvc_version = msvc_versions[python_major_minor]
    compiler_year = {
        '10.0': '2010',
        '11.0': '2012',
        '12.0': '2013',
        '14.0': '2015',
        '14.1': '2017',
        '14.14': '2017',
    }[msvc_version]
    if decimal.Decimal(msvc_version) >= 14.1:
        vs_path = os.path.join(
            'C:/',
            'Program Files (x86)',
            'Microsoft Visual Studio',
            compiler_year,
            'Community',
        )
    else:
        vs_path = os.path.join(
            'C:/', 'Program Files (x86)', 'Microsoft Visual Studio {}'.format(
                msvc_version
            )
        )

    vcvarsall = os.path.join(vs_path, 'VC')
    if decimal.Decimal(msvc_version) >= 14.1:
        vcvarsall = os.path.join(vcvarsall, 'Auxiliary', 'Build')
    vcvarsall = os.path.join(vcvarsall, 'vcvarsall.bat')

    os.environ = get_environment_from_batch_command(
        [
            vcvarsall,
            {32: 'x86', 64: 'x64'}[bits]
        ],
        initial=os.environ
    )
    print('  ---- os.environ:')
    for k, v in os.environ.items():
        print('    {}: {}'.format(k, v))

    compiler_name = 'msvc'
    compiler_bits_string = {32: '', 64: '_64'}[bits]

    compiler_dir = ''.join((compiler_name, compiler_year, compiler_bits_string))

    qt_bin_path = os.path.join(os.environ['QT_BASE_PATH'], compiler_dir, 'bin')
    os.environ['PATH'] = os.pathsep.join((os.environ['PATH'], qt_bin_path))

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

    build = os.environ['APPVEYOR_BUILD_FOLDER']

    destination = os.path.join(build, 'pyqt5-tools')
    os.makedirs(destination, exist_ok=True)

    build_id = os.environ['APPVEYOR_BUILD_ID']
    with open(os.path.join(destination, 'build_id'), 'w') as f:
        f.write(build_id + '\n')

    job_id = os.environ['APPVEYOR_JOB_ID']
    with open(os.path.join(destination, 'job_id'), 'w') as f:
        f.write(job_id + '\n')

    windeployqt_path = os.path.join(qt_bin_path, 'windeployqt.exe')

    application_paths = glob.glob(os.path.join(qt_bin_path, '*.exe'))

    os.makedirs(destination, exist_ok=True)

    for application in application_paths:
        application_path = os.path.join(qt_bin_path, application)

        print('\n\nChecking: {}'.format(os.path.basename(application)))
        try:
            output = subprocess.check_output(
                [
                    windeployqt_path,
                    application_path,
                    '--dry-run',
                    '--list', 'source',
                ],
                cwd=destination,
            )
        except subprocess.CalledProcessError:
            continue

        if b'WebEngine' in output:
            print('    skipped')
            continue

        shutil.copy(application_path, destination)

        report_and_check_call(
            command=[
                windeployqt_path,
                os.path.basename(application),
            ],
            cwd=destination,
        )

    application_names = [
        pathlib.Path(application).stem
        for application in application_paths
    ]

    entry_points_py = pathlib.Path(destination)/'entrypoints.py'
    shutil.copy(
        pathlib.Path(__file__).with_name('entrypoints.py'),
        entry_points_py,
    )
    with open(entry_points_py, 'a') as f:
        for name in application_names:
            f.write(textwrap.dedent('''\
            def {name}():
                return subprocess.call([here/'{name}.exe', *sys.argv])


            '''.format(name=name)))

    console_scripts = [
        '{name} = pyqt5_tools.entrypoints:{name}'.format(name=name)
        for name in application_names
    ]

    platform_path = os.path.join(destination, 'platforms')
    os.makedirs(platform_path, exist_ok=True)
    for platform_plugin in ('minimal',):
        shutil.copy(
            os.path.join(
                os.environ['QT_BASE_PATH'],
                compiler_dir,
                'plugins',
                'platforms',
                'q{}.dll'.format(platform_plugin),
            ),
            platform_path,
        )

    sysroot = os.path.join(build, 'sysroot')
    os.makedirs(sysroot)
    nmake = shutil.which('nmake')

    src = os.path.join(build, 'src')
    os.makedirs(src)
    native = os.path.join(sysroot, 'native')
    os.makedirs(native)

    pyqt5_version = os.environ['PYQT5_VERSION']
    # sip_version = next(
    #     d.version
    #     for d in pip.utils.get_installed_distributions()
    #     if d.project_name == 'sip'
    # )
    sip_version = {
        '5.5.1': '4.17',
        '5.6': '4.19',
        '5.7.1': '4.19.8',
        '5.8.2': '4.19.8',
        '5.9': '4.19.8',
        '5.9.2': '4.19.8',
        '5.10': '4.19.8',
        '5.10.1': '4.19.8',
        '5.11.2': '4.19.13.dev1808131137',
    }[pyqt5_version]

    sip_name = 'sip-{}'.format(sip_version)
    if 'dev' in sip_version:
        sip_url = (
            'https://www.riverbankcomputing.com'
            '/static/Downloads/sip/sip-{}.zip'.format(sip_version)
        )
    else:
        sip_url = (
            'http://downloads.sourceforge.net'
            '/project/pyqt/sip/sip-{}/{}.zip'.format(
                sip_version, sip_name
            )
        )

    r = requests.get(sip_url)

    z = zipfile.ZipFile(io.BytesIO(r.content))
    z.extractall(path=src)
    sip = os.path.join(src, sip_name)
    native_sip = sip + '-native'
    shutil.copytree(os.path.join(src, sip_name), native_sip)
    os.environ['CL'] = '/I"{}\\include\\python{}"'.format(
        sysroot,
        '.'.join(python_major_minor)
    )

    year = compiler_year
    if year == '2013':
        year = '2010'

    pyqt5_version_tuple = tuple(int(x) for x in pyqt5_version.split('.'))

    report_and_check_call(
        command=[
            os.path.join(os.environ['PYTHON'], 'python'),
            'configure.py',
        ],
        cwd=native_sip,
    )
    report_and_check_call(
        command=[
            nmake,
        ],
        cwd=native_sip,
        env=os.environ,
    )
    report_and_check_call(
        command=[
            nmake,
            'install',
        ],
        cwd=native_sip,
        env=os.environ,
    )

    sip_configure_extras = []
    if pyqt5_version_tuple >= (5, 11):
        sip_configure_extras.append('--sip-module=PyQt5.sip')

    report_and_check_call(
        command=[
            os.path.join(os.environ['PYTHON'], 'python'),
            'configure.py',
            '--no-tools',
            *sip_configure_extras,
        ],
        cwd=sip,
    )

    report_and_check_call(
        command=[
            nmake,
        ],
        cwd=sip,
        env=os.environ,
    )

    report_and_check_call(
        command=[
            nmake,
            'install',
        ],
        cwd=sip,
        env=os.environ,
    )

    if tuple(int(x) for x in pyqt5_version.split('.')) >= (5, 6):
        pyqt5_name = 'PyQt5_gpl-{}'.format(pyqt5_version)
    else:
        pyqt5_name = 'PyQt-gpl-{}'.format(pyqt5_version)

    r = requests.get(
        'http://downloads.sourceforge.net'
        '/project/pyqt/PyQt5/PyQt-{}/{}.zip'.format(
            pyqt5_version, pyqt5_name
        )
    )
    z = zipfile.ZipFile(io.BytesIO(r.content))
    z.extractall(path=src)

    pyqt5 = os.path.join(src, pyqt5_name)

    # TODO: make a patch for the lower versions as well
    if pyqt5_version_tuple >= (5, 7):
        if pyqt5_version_tuple >= (5, 11):
            pluginloader_patch = '..\\..\\pluginloader.5.11.patch'
        else:
            pluginloader_patch = '..\\..\\pluginloader.patch'

        report_and_check_call(
            command='patch -p 1 -i {}'.format(pluginloader_patch),
            shell=True, # TODO: don't do this
            cwd=pyqt5,
        )

    designer_pro = os.path.join(pyqt5, 'designer', 'designer.pro-in')
    with open(designer_pro, 'a') as f:
        f.write('\nDEFINES     += PYTHON_LIB=\'"\\\\\\"@PYSHLIB@\\\\\\""\'\n')
    command = [
        os.path.join(os.environ['PYTHON'], 'python'),
        'configure.py',
        '--no-tools',
        '--no-qsci-api',
        '--no-qml-plugin',
        '--confirm-license',
        '--designer-plugindir={}'.format(
            os.path.join(sysroot, 'pyqt5-install', 'designer'),
        ),
        '--enable=QtDesigner',
        '--verbose',
    ]

    report_and_check_call(
        command=command,
        cwd=pyqt5,
        env=os.environ,
    )

    sys.stderr.write('another stderr test from {}\n'.format(__file__))

    report_and_check_call(
        command=[
            nmake,
        ],
        cwd=pyqt5,
        env=os.environ,
    )
    report_and_check_call(
        command=[
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
    redist_path = os.path.join(vs_path, 'VC', 'redist')\

    if decimal.Decimal(msvc_version) >= 14.1:
        redist_path = os.path.join(redist_path, 'MSVC')
        hmm, = os.listdir(redist_path)
        redist_path = os.path.join(redist_path, hmm)

    msvc_version_for_files = {'14.14': '14.1'}.get(msvc_version, msvc_version)
    msvc_version_for_files = msvc_version_for_files.replace('.', '')

    redist_path = os.path.join(
        redist_path,
        plat,
        'Microsoft.VC{}.CRT'.format(msvc_version_for_files),
    )

    redist_files = os.listdir(redist_path)

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

    return Results(console_scripts=console_scripts)


if __name__ == '__main__':
    sys.exit(main())
