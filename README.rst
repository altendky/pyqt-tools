==========
pyqt-tools
==========

This repository holds four packages that together provide Qt Designer and the
other Qt tools for use with PyQt.  Each package is built and published to PyPI
separately, for both Qt 5 and Qt 6.

.. list-table::
   :header-rows: 1

   * - Directory
     - PyPI packages
     - Purpose
   * - `packages/qt-applications`_
     - qt5-applications, qt6-applications
     - The Qt applications themselves
   * - `packages/qt-tools`_
     - qt5-tools, qt6-tools
     - Wrappers for running the Qt applications
   * - `packages/pyqt-plugins`_
     - pyqt5-plugins, pyqt6-plugins
     - The PyQt Designer and QML plugins
   * - `packages/pyqt-tools`_
     - pyqt5-tools, pyqt6-tools
     - Wrappers for Designer and QML tools with the PyQt plugins enabled

Each package depends on the one listed above it.  Most users want pyqt5-tools
or pyqt6-tools; see `packages/pyqt-tools`_ for installation and usage.

These packages were previously developed in the separate qt-applications,
qt-tools, and pyqt-plugins repositories, whose full histories were merged in
here.  Package tags are prefixed with the directory name, for example
``qt-tools-v1.3``.  To view a file's history from before the move, pass both
paths, for example ``git log -- packages/qt-tools/setup.py setup.py``.

Licensing differs between packages; see the ``COPYING`` file in each package
directory.

Releases are made through pull requests opened with ``mise run release``, for
example ``mise run release qt-tools=1.4``.  CI then tags, publishes, and opens a
pull request for the next development versions.  See `docs/release.md`_.

.. _`packages/qt-applications`: packages/qt-applications
.. _`packages/qt-tools`: packages/qt-tools
.. _`packages/pyqt-plugins`: packages/pyqt-plugins
.. _`packages/pyqt-tools`: packages/pyqt-tools
.. _`docs/release.md`: docs/release.md
