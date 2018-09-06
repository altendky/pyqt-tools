from __future__ import print_function

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

    subprocess.check_call(
        [
            'twine',
            'upload',
            '*.whl',
        ],
    )


if __name__ == '__main__':
    sys.exit(main())
