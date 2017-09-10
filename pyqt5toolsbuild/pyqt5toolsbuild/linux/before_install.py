import os
import shutil
import subprocess

from .. import utils


def deploy_qt(linuxdeployqt_path, qt_bin_path, deployed_qt_path):
    skipped = []

    try:
        applications = os.listdir(qt_bin_path)
    except FileNotFoundError:
        utils.list_missing_directories(qt_bin_path)
        raise

    for application in applications:
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

    if not os.path.isfile(os.path.join('deployed_qt', 'designer')):
        qt_bin_path = utils.qt_bin_path(qt_version)

        deploy_qt(
            linuxdeployqt_path=linuxdeployqt_path,
            qt_bin_path=qt_bin_path,
            deployed_qt_path=deployed_qt_path,
        )
