import os
import shutil
import stat
import subprocess
import tempfile

from .. import utils


def install_qt(path, version):
    installed_path = os.path.join(path, 'Qt')
    shutil.rmtree(installed_path)

    file_name = 'qt-opensource-linux-x64-{}.run'.format(version.exactly(3))
    url = ''.join((
        'http://download.qt.io',
        '/official_releases/qt/{}/{}/'.format(
            version.exactly(2),
            version.exactly(3),
        ),
        file_name,
    ))

    installer_path = utils.save_url_to_file(
        url=url,
        file_path=path,
        file_name=file_name,
    )

    os.chmod(installer_path, stat.S_IXUSR)

    utils.report_and_check_call(
        command=[
            installer_path,
            ' --platform minimal',
            '--script', 'qt-installer-noninteractive.qs',
            '--no-force-installations',
        ],
        cwd=path,
    )

    return installed_path


def deploy_qt(linuxdeployqt_path, qt_bin_path, deployed_qt_path):
    skipped = []
    for application in os.listdir(qt_bin_path):
        application_path = os.path.join(qt_bin_path, application)

        shutil.copy(application_path, deployed_qt_path)

        try:
            utils.report_and_check_call(
                command=[
                    linuxdeployqt_path,
                    application,
                    '-qmake={}'.format(os.path.join(qt_bin_path, 'qmake')),
                ],
                cwd=deployed_qt_path,
            )
        except subprocess.CalledProcessError:
            print('FAILED SO SKIPPING: {}'.format(application))
            os.remove(os.path.join(deployed_qt_path, application))
            skipped.append(application)
    os.remove(os.path.join(deployed_qt_path, 'AppRun'))
    print('\nSkipped: ')
    print('\n'.join('    {}'.format(a for a in sorted(skipped))))
    print()


def main():
    build_path = os.environ['TRAVIS_BUILD_DIR']
    deployed_qt_path = os.path.join(build_path, 'deployed_qt')
    os.makedirs(deployed_qt_path, exist_ok=True)

    pyqt5_version = utils.Version.from_string(os.environ['PYQT5_VERSION'])
    qt_version = utils.pyqt_to_qt_version(pyqt5_version)

    linuxdeployqt_path = os.path.join(
        build_path,
        'linuxdeployqt',
        'usr',
        'bin',
        'linuxdeployqt',
    )

    with tempfile.TemporaryDirectory() as temp_path:
        if not os.path.isfile(os.path.join('deployed_qt', 'designer')):
            qt_path = install_qt(temp_path, qt_version)
            qt_bin_path = os.path.join(qt_path, str(qt_version), 'gcc_64', 'bin')

            deploy_qt.deploy_qt(
                linuxdeployqt_path=linuxdeployqt_path,
                qt_bin_path=qt_bin_path,
                deployed_qt_path=deployed_qt_path,
            )
