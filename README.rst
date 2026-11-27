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
     - Wrappers for Designer and QML tools, with the PyQt plugins enabled by
       the optional ``plugins`` extra

Each package depends on the one listed above it, except that pyqt-tools
depends on pyqt-plugins only through its ``plugins`` extra.  Most users want
pyqt5-tools or pyqt6-tools; see `packages/pyqt-tools`_ for installation and
usage.

These packages were previously developed in the separate qt-applications,
qt-tools, and pyqt-plugins repositories, whose full histories were merged in
here.  Package tags are prefixed with the directory name, for example
``qt-tools-v1.3``.  To view a file's history from before the move, pass both
paths, for example ``git log -- packages/qt-tools/setup.py setup.py``.

Licensing differs between packages; see the ``COPYING`` file in each package
directory.

.. _`packages/qt-applications`: packages/qt-applications
.. _`packages/qt-tools`: packages/qt-tools
.. _`packages/pyqt-plugins`: packages/pyqt-plugins
.. _`packages/pyqt-tools`: packages/pyqt-tools
