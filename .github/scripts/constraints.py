"""Print pip constraints pinning the exact version of every wheel found in the
given directories, so that wheels built earlier in the same CI run are used
instead of releases from PyPI."""

import pathlib
import sys


def main(directories):
    for directory in directories:
        for wheel in sorted(pathlib.Path(directory).glob("*.whl")):
            name, version = wheel.name.split("-")[:2]
            print(f"{name}=={version}")


main(sys.argv[1:])
