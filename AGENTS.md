# Agent context

Start with [the README](README.rst) for what each package provides.

The four packages under `packages/` are published separately, each as Qt 5 and
Qt 6 variants, and depend on each other in this order: `qt-applications`,
`qt-tools`, `pyqt-plugins`, `pyqt-tools`. Qt, PyQt and the Python and platform
matrix are chosen in `.github/ci-config.json`. Each package takes its version
from tags with its own prefix, such as `qt-tools-v1.4`.

Install the repository tools with `mise install --locked` and run
`pre-commit run --all-files` before pushing. Building and testing the packages
needs Qt and the build platforms, so CI is the source of truth for those.
