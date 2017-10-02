import io
import os
import platform
import shutil
import sys

import click

import pyqt5toolsbuild.utils


@click.command()
def main():
    build_venv_bin = os.path.dirname(sys.executable)
    build_python_path = sys.executable
    build_pyqtdeploycli_path = os.path.join(build_venv_bin, 'pyqtdeploycli')

    build = os.environ['TRAVIS_BUILD_DIR']
    deployed_qt = os.path.join(build, 'deployed_qt')
    destination = os.path.join(build, 'pyqt5-tools')
    src_path = os.path.join(build, 'src')
    sysroot = os.path.join(build, 'sysroot')
    native_sysroot = os.path.join(sysroot, 'native')

    os.makedirs(sysroot)
    os.makedirs(native_sysroot)
    os.makedirs(src_path)

    bits = int(platform.architecture()[0][0:2])
    # TODO: use full version info
    python_version = pyqt5toolsbuild.utils.Version.from_sequence(
        sys.version_info.major,
        sys.version_info.minor,
        sys.version_info.micro,
    )

    print('copying {}'.format(deployed_qt))
    print('     to {}'.format(destination))
    shutil.copytree(deployed_qt, destination)

    pyqt5_version = pyqt5toolsbuild.utils.Version.from_string(
        os.environ['PYQT5_VERSION'],
    )
    qt_version = pyqt5toolsbuild.utils.pyqt_to_qt_version(pyqt5_version)

    qt_bin_path = os.path.join(pyqt5toolsbuild.utils.qt_path(qt_version), 'bin')
    qmake = os.path.join(qt_bin_path, 'qmake')
    make = 'make'

    qt_version = pyqt5toolsbuild.utils.pyqt_to_qt_version(pyqt5_version)
    sip_version = pyqt5toolsbuild.utils.pyqt_to_sip_version(pyqt5_version)
    python_version = pyqt5toolsbuild.utils.python_version()

    python_name, python_url = pyqt5toolsbuild.utils.python_name_url(
        python_version
    )
    python_path = os.path.join(src_path, python_name)

    pyqt5toolsbuild.utils.extract_tar_url(
        url=python_url,
        destination=src_path,
    )

    pyqt5toolsbuild.utils.report_and_check_call(
        command=[
            build_pyqtdeploycli_path,
            '--package', 'python',
            '--target', 'linux-{}'.format(bits),
            'configure',
        ],
        cwd=python_path,
    )

    pyqt5toolsbuild.utils.report_and_check_call(
        command=[
            qmake,
            'SYSROOT={}'.format(sysroot),
        ],
        cwd=python_path,
    )

    pyqt5toolsbuild.utils.report_and_check_call(
        command=[
            make,
        ],
        cwd=python_path,
    )

    pyqt5toolsbuild.utils.report_and_check_call(
        command=[
            make,
            'install',
        ],
        cwd=python_path,
    )

    os.environ['CL'] = '/I"{}"'.format(os.path.join(
        sysroot,
        'include',
        'python{}'.format('.'.join(str(python_version.exactly(2)))),
    ))

    sip_name, sip_url = pyqt5toolsbuild.utils.sip_name_url(sip_version)
    sip_path = os.path.join(src_path, sip_name)
    native_sip_path = sip_path + '-native'

    pyqt5toolsbuild.utils.extract_zip_url(
        url=sip_url,
        destination=src_path,
    )

    shutil.copytree(sip_path, native_sip_path)

    pyqt5toolsbuild.utils.report_and_check_call(
        command=[
            build_python_path,
            'configure.py',
            '--static',
            '--sysroot={}'.format(native_sysroot),
            '--platform=linux-g++',
            '--target-py-version={}'.format(str(python_version.exactly(2))),
        ],
        cwd=native_sip_path,
    )
    pyqt5toolsbuild.utils.report_and_check_call(
        command=[
            make,
        ],
        cwd=native_sip_path,
        env=os.environ,
    )
    pyqt5toolsbuild.utils.report_and_check_call(
        command=[
            make,
            'install',
        ],
        cwd=native_sip_path,
        env=os.environ,
    )

    pyqt5toolsbuild.utils.report_and_check_call(
        command=[
            build_pyqtdeploycli_path,
            '--package', 'sip',
            '--target', 'linux-{}'.format(bits),
            'configure',
        ],
        cwd=sip_path,
    )

    pyqt5toolsbuild.utils.report_and_check_call(
        command=[
            build_python_path,
            'configure.py',
            '--static',
            '--sysroot={}'.format(sysroot),
            '--no-tools',
            '--use-qmake',
            '--configuration=sip-linux.cfg',
            '--platform=linux-g++',
            '--target-py-version={}'.format(str(python_version.exactly(2))),
        ],
        cwd=sip_path,
    )

    pyqt5toolsbuild.utils.report_and_check_call(
        command=[
            qmake,
        ],
        cwd=sip_path,
        env=os.environ,
    )

    pyqt5toolsbuild.utils.report_and_check_call(
        command=[
            make,
        ],
        cwd=sip_path,
        env=os.environ,
    )

    pyqt5toolsbuild.utils.report_and_check_call(
        command=[
            make,
            'install',
        ],
        cwd=sip_path,
        env=os.environ,
    )

    pyqt5_name, pyqt5_url = pyqt5toolsbuild.utils.pyqt5_name_url(pyqt5_version)

    pyqt5toolsbuild.utils.extract_zip_url(
        url=pyqt5_url,
        destination=src_path,
    )

    pyqt5_path = os.path.join(src_path, pyqt5_name)

    # TODO: enable the patch
    # # TODO: make a patch for the lower versions as well
    # if tuple(int(x) for x in pyqt5_version.split('.')) >= (5, 7):
    #     report_and_check_call(
    #         command='patch -p 1 < ..\\..\\pluginloader.patch',
    #         shell=True, # TODO: don't do this
    #         cwd=pyqt5,
    #     )

    pyqt5toolsbuild.utils.report_and_check_call(
        command=[
            build_pyqtdeploycli_path,
            '--package', 'pyqt5',
            '--target', 'win-{}'.format(bits),
            'configure',
        ],
        cwd=pyqt5_path,
    )
    pyqt5_cfg = os.path.join(pyqt5_path, 'pyqt5-win.cfg')
    with open(pyqt5_cfg) as f:
        original = io.StringIO(f.read())
    with open(pyqt5_cfg, 'w') as f:
        f.write('\npy_pyshlib = python{}.dll\n'.format(
            python_version.exactly(2),
        ))
        for line in original:
            if line.startswith('py_pylib_lib'):
                f.write('py_pylib_lib = python%(py_major)%(py_minor)\n')
            else:
                f.write(line)
    designer_pro = os.path.join(pyqt5_path, 'designer', 'designer.pro-in')
    with open(designer_pro, 'a') as f:
        f.write('\nDEFINES     += PYTHON_LIB=\'"\\\\\\"@PYSHLIB@\\\\\\""\'\n')
    command = [
        build_python_path,
        r'configure.py',
        r'--static',
        r'--sysroot={}'.format(sysroot),
        r'--no-tools',
        r'--no-qsci-api',
        r'--no-qml-plugin',
        r'--configuration={}'.format(pyqt5_cfg),
        r'--confirm-license',
        r'--sip={}'.format(os.path.join(sysroot, 'native', 'bin', 'sip')),
        r'--bindir={}\pyqt5-install\bin'.format(sysroot),
        r'--destdir={}\pyqt5-install\dest'.format(sysroot),
        r'--designer-plugindir={}\pyqt5-install\designer'.format(sysroot),
        r'--enable=QtDesigner',
        '--target-py-version={}'.format(str(python_version.exactly(2))),
    ]

    if pyqt5_version >= pyqt5toolsbuild.utils.Version.from_sequence(5, 6):
        command.append(r'--qmake={}'.format(qmake))

    pyqt5toolsbuild.utils.report_and_check_call(
        command=command,
        cwd=pyqt5_path,
        env=os.environ,
    )
    pyqt5toolsbuild.utils.report_and_check_call(
        command=[
            qmake
        ],
        cwd=pyqt5_path,
        env=os.environ,
    )

    sys.stderr.write('another stderr test from {}\n'.format(__file__))

    pyqt5toolsbuild.utils.report_and_check_call(
        command=[
            make,
        ],
        cwd=pyqt5_path,
        env=os.environ,
    )
    pyqt5toolsbuild.utils.report_and_check_call(
        command=[
            make,
            'install',
        ],
        cwd=pyqt5_path,
        env=os.environ,
    )
