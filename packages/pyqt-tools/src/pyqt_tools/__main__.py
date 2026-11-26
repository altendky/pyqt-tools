""" Enables support for calling entrypoints using `python -m`.

Examples:
    Launching PyQt6 designer: `python -m pyqt6_tools designer`
    Launching PyQt5 designer: `python -m pyqt5_tools designer`
"""


import sys
from . import entrypoints

sys.exit(entrypoints.main())
