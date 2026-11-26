from __future__ import print_function

import glob
import os
import subprocess
import sys


def main():
    no_tag = subprocess.call(
        [
            'git',
            'describe',
            '--tags',
            '--candidates',
            '0',
        ],
    )

    if no_tag:
        print('No tag found, doing nothing.')
        return

    print('Tag found, uploading to PyPI.')

    wheels = glob.glob(os.path.join('dist', '*.whl'))

    subprocess.check_call(
        [
            sys.executable,
            '-m', 'twine',
            'upload',
            *wheels,
        ],
    )


if __name__ == '__main__':
    sys.exit(main())
