#!/usr/bin/env python3

import collections
#import git
import os

from datetime import datetime, timezone


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
if status.prerelease_suffix is not None:
    prerelease_list = []
    local_time = datetime.now(timezone.utc).astimezone()
    timestamp = local_time.isoformat()
    timestamp = timestamp.replace('-', '', 2)
    timestamp = timestamp.replace(':', '')
    prerelease_list.append(timestamp)

#    repo = git.Repo(os.getcwd())
#    sha = repo.head.object.hexsha
#    prerelease_list.append(sha)
#    if repo.is_dirty():
#        prerelease_list.append('dirty')

    prerelease_str = '-'.join(prerelease_list)

version_numbers = [5, 7]

version_str = (
    '.'.join([str(v) for v in version_numbers])
    + status.prerelease_suffix
    # TODO: this is totally cheating, revisit the revision scheme
    + '5'# prerelease_str
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
