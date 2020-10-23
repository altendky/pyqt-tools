import os
import subprocess
import sys

import qttools


fspath = getattr(os, 'fspath', str)


# def designer():
#     env = qttools.create_environment(reference=os.environ)
#
#     completed_process = subprocess.run(
#         [
#             fspath(qttools.application_path('designer')),
#             *sys.argv[1:],
#         ],
#         env=env,
#     )
#
#     sys.exit(completed_process.returncode)
