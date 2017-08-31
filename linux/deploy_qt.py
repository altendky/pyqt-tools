import os
import shutil
import subprocess
import sys


def report_and_check_call(**kwargs):
    print('\nCalling: ')

    for kwarg in ('command', 'cwd'):
        if kwarg in kwargs:
            print('    {}: {}'.format(kwarg, kwargs[kwarg]))

    # may only be required on AppVeyor
    sys.stdout.flush()

    command = kwargs.pop('command')

    subprocess.check_call(command, **kwargs)


def main():
    build = os.environ['TRAVIS_BUILD_DIR']
    qt_bin_path = os.path.join(build, 'Qt', '5.9.1', 'gcc_64', 'bin')
    deployed_qt = os.path.join(build, 'deployed_qt')
    os.makedirs(deployed_qt, exist_ok=True)

    deployqt_path = os.path.join(
        build,
        'linuxdeployqt',
        'usr',
        'bin',
        'linuxdeployqt',
    )

    skipped = []

    for application in os.listdir(qt_bin_path):
        application_path = os.path.join(qt_bin_path, application)

        shutil.copy(application_path, deployed_qt)

        try:
            report_and_check_call(
                command=[
                    deployqt_path,
                    application,
                    '-qmake={}'.format(os.path.join(qt_bin_path, 'qmake')),
                ],
                cwd=deployed_qt,
            )
        except subprocess.CalledProcessError:
            print('FAILED SO SKIPPING: {}'.format(application))
            os.remove(os.path.join(deployed_qt, application))
            skipped.append(application)

    os.remove(os.path.join(deployed_qt, 'AppRun'))

    print('\nSkipped: ')
    print('\n'.join('    {}'.format(a for a in sorted(skipped))))
    print()

    report_and_check_call(
        command=[
            'tree'
        ],
        cwd=deployed_qt,
    )


if __name__ == '__main__':
    sys.exit(main())
