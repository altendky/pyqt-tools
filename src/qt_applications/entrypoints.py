import functools
import os
import subprocess
import sys

import qt_applications


fspath = getattr(os, 'fspath', str)


def run(application_name, environment=os.environ):
    modified_environment = qt_applications.create_environment(reference=environment)
    application_path = qt_applications.application_path(application_name)

    completed_process = subprocess.run(
        [
            fspath(application_path),
            *sys.argv[1:],
        ],
        env=modified_environment,
    )

    sys.exit(completed_process.returncode)


# designer = functools.partial(run, application_name='designer')
