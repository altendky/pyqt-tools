#!/usr/bin/env python3

import collections


DevelopmentStatus = collections.namedtuple(
    'DevelopmentStatus',
    [
        'prerelease_suffix',
        'classifier'
    ]
)

# Development Status :: 1 - Planning
# Development Status :: 6 - Mature
# Development Status :: 7 - Inactive

statuses = {
    'dev': DevelopmentStatus(
        prerelease_suffix='.dev',
        classifier='Development Status :: 2 - Pre-Alpha'
    ),
    'alpha': DevelopmentStatus(
        prerelease_suffix='.a',
        classifier='Development Status :: 3 - Alpha'
    ),
    'beta': DevelopmentStatus(
        prerelease_suffix='.b',
        classifier='Development Status :: 4 - Beta'
    ),
    'stable': DevelopmentStatus(
        prerelease_suffix=None,
        classifier='Development Status :: 5 - Production/Stable'
    ),
}

status_type = 'dev'
status = statuses[status_type]
prerelease_str = 'add-build-hash-here'

if (status.prerelease_suffix is None and
    (prerelease_str is not None or len(prerelease_str) > 0)):
    raise Exception("prerelease_str must be empty for status '{}'"
                    .format(status_type))

version_numbers = [5, 7]

version_str = (
    '.'.join([str(v) for v in version_numbers])
    + status.prerelease_suffix
    + prerelease_str
)

directories = [
    'PyQt5-tools'
]

data_files_list = []
for directory in directories:
    all_files = []
    for root, dirs, files in os.walk('PyQt5-tools'):
        all_files.extend([os.path.join(root, file) for file in files])
    data_files_list.append((directory, all_files))


def version():
    return version_str

def data_files():
    return data_files_list
    
#def format(string):
#    return string.format(**globals())
