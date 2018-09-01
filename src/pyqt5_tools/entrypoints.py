import pathlib
import subprocess
import sys


here = pathlib.Path(__file__).parent


def pyqt5toolsinstalluic():
    destination = here/'bin'
    destination.mkdir(parents=True, exist_ok=True)
    there = pathlib.Path(sys.executable).parent

    shutil.copy(str(there/'pyuic5.exe'), str(destination/'uic.exe'))

# def designer():
#     return subprocess.call([str(here/'designer.exe'), *sys.argv[1:]])

