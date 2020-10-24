import functools
import os
import subprocess
import sys

import qttools


fspath = getattr(os, 'fspath', str)


def run(application_name, environment=os.environ):
    modified_environment = qttools.create_environment(reference=environment)
    application_path = qttools.application_path(application_name)

    completed_process = subprocess.run(
        [
            fspath(application_path),
            *sys.argv[1:],
        ],
        env=modified_environment,
    )

    sys.exit(completed_process.returncode)


# designer = functools.partial(run, application_name='designer')
