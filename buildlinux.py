import os
import shutil
import subprocess
import sys


def report_and_check_call(command, *args, **kwargs):
    print('\nCalling: {}'.format(command))
    # may only be required on AppVeyor
    sys.stdout.flush()
    subprocess.check_call(command, *args, **kwargs)


def main():
    print('in {}'.format(__file__))
    qt_bin_path = os.path.join('Qt', '5.9.1', 'gcc_64', 'bin')

    build = os.environ['TRAVIS_BUILD_DIR']
    destination = os.path.join(build, 'pyqt5-tools')
    os.makedirs(destination, exist_ok=True)

    deployqt_path = os.path.join(
        build,
        'linuxdeployqt',
        'usr',
        'bin',
        'linuxdeployqt',
    )

    for application in os.listdir(qt_bin_path):
        application_path = os.path.join(qt_bin_path, application)

        shutil.copy(application_path, destination)

        report_and_check_call(
            command=[
                deployqt_path,
                application,
                '-qmake={}'.format(os.path.join(qt_bin_path, 'qmake')),
            ],
            cwd=destination,
        )

    report_and_check_call(
        command=[
            'tree'
        ],
        cwd=destination,
    )


if __name__ == '__main__':
    sys.exit(main())
