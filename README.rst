==========
pyqt-tools
==========


|PyPI| |Pythons| |GitHub|

The PyQt6 wheels do not provide tools such as Qt Designer that were included in
the old binary installers. This package aims to provide those in a separate
package which is useful for developers while the official PyQt6 wheels stay
focused on fulfilling the dependencies of PyQt6 applications.

Both Windows and Linux are supported.  Adjust paths etc accordingly if applying
the explanations below in Linux rather than Windows.  macOS support is
incomplete but see `issue #12`_ if you want to discuss it.

.. |PyPI| image:: https://img.shields.io/pypi/v/pyqt6-tools.svg
   :alt: PyPI version
   :target: https://pypi.org/project/pyqt6-tools/

.. |Pythons| image:: https://img.shields.io/pypi/pyversions/pyqt6-tools.svg
   :alt: supported Python versions
   :target: https://pypi.org/project/pyqt6-tools/

.. |GitHub| image:: https://img.shields.io/github/last-commit/altendky/pyqt-tools/main.svg
   :alt: source on GitHub
   :target: https://github.com/altendky/pyqt-tools

.. _`issue #12`: https://github.com/altendky/pyqt-tools/issues/12

------------
Installation
------------

.. code-block:: powershell

  yourenv/Scripts/pip.exe install pyqt6-tools~=6.4

You will generally install pyqt6-tools using ``pip install``.  In most cases
you should be using virtualenv_ or venv_ to create isolated environments to
install your dependencies in.  The above command assumes an env in the
directory ``yourenv``.  The ``~=6.4`` specifies a `release compatible with`_
6.4 which will be the latest version of pyqt6-tools built for PyQt6_ 6.4. If
you are using a different PyQt6 version, specify it instead of 6.4.  PyPI
keeps a list of `all available versions`_.

.. _virtualenv: https://virtualenv.pypa.io/en/stable/
.. _venv: https://docs.python.org/3/library/venv.html
.. _PyQt6: https://pypi.org/project/PyQt6/
.. _`release compatible with`: https://www.python.org/dev/peps/pep-0440/#compatible-release
.. _`all available versions`: https://pypi.org/project/pyqt6-tools/#history

Note:
    As of pyqt6-tools v3 the package has been broken down into four pieces.
    The wrappers remain here but the plugins are located in pyqt6-plugins_,
    some Qt application helpers in qt6-tools_, and the applications are in
    qt6-applications_.

.. _pyqt6-plugins: https://github.com/altendky/pyqt-plugins
.. _qt6-tools: https://github.com/altendky/qt-tools
.. _qt6-applications: https://github.com/altendky/qt-applications

-----
Usage
-----

A program is provided available as ``Scripts/pyqt6-tools.exe``.  There are
subcommands provided for each of Designer, QML Scene, and the QML Test Runner.
These wrapper commands provide additional functionality related to launching
the underlying programs.  A larger set of Qt application are available as
subcommands of the ``Scripts/qt6-tools.exe`` program.  In both cases, passing
``--help`` will list the available subcommands.

Additionally, each ``pyqt6-tools`` subcommand listed below includes a parameter
to run a basic example which can be used to see if the plugins are working.
These examples are `not` intended to be used as examples of good code.

Each subcommand searches up the filesystem tree from your current
working directory to find a ``.env`` file and loads it if found.  If found, the
environment variable ``DOT_ENV_DIRECTORY`` will be set to the directory
containing the ``.env`` file.  With this extra variable you can specify paths
relative to the ``.env`` location.

.. code-block:: powershell

  PYQTDESIGNERPATH=${PYQTDESIGNERPATH};${DOT_ENV_DIRECTORY}/path/to/my/widgets


Designer
========

There is a ``Scripts/pyqt6-tools.exe designer.exe`` entry point that will help fill out
``PYQTDESIGNERPATH`` from either command line arguments or a ``.env`` file.
Unknown arguments are passed through to the original Qt Designer program.

.. code-block::

    Usage: pyqt6-tools designer [OPTIONS]

    Options:
      -p, --widget-path DIRECTORY     Paths to be combined with PYQTDESIGNERPATH
      --example-widget-path           Include the path for the pyqt6-tools example
                                      button (c:\users\sda\testenv\lib\site-
                                      packages\pyqt6_plugins)

      --designer-help                 Pass through to get Designer's --help
      --test-exception-dialog         Raise an exception to check the exception
                                      dialog functionality.

      --qt-debug-plugins / --no-qt-debug-plugins
                                      Set QT_DEBUG_PLUGINS=1
      --help                          Show this message and exit.

If you want to view the generated code from within Designer, you can
run ``Scripts/pyqt6-tools.exe installuic`` and it will copy ``pyuic6.exe``
such that Designer will use it and show you generated Python code.  Note that
this will enable viewing using the C++ menu item while the Python menu item
will be broken.  Without having made this adjustment, the C++ option shows
C++ code while the Python option shows PySide2 code.  ``pyqt6`` must already
be installed or this script will be unable to find the original ``pyuic6.exe``
to copy.

In addition to the standard features of the official Designer plugin, this
provides an exception dialog for your widget's Python code.  Otherwise Designer
in Windows silently crashes on Python exceptions.

QML Plugin
==========

The QML plugin is also included.  In the future a tool may be provided to
handle copying of the plugin to each directory where it is needed.  For now
this must be done manually.

``site-packages/pyqt6_tools/Qt/bin/plugins/pyqt6qmlplugin.dll``

QML Scene
=========

.. code-block::

    Usage: pyqt6-tools qmlscene [OPTIONS]

    Options:
      -p, --qml2-import-path DIRECTORY
                                      Paths to be combined with QML2_IMPORT_PATH
      --qmlscene-help                 Pass through to get QML scene's --help
      --qt-debug-plugins / --no-qt-debug-plugins
                                      Set QT_DEBUG_PLUGINS=1
      --run-qml-example               Run the pyqt6-tools QML example
      --help                          Show this message and exit.

QML Test Runner
===============

.. code-block::

    Usage: pyqt6-tools qmltestrunner [OPTIONS]

    Options:
      -p, --qml2-import-path DIRECTORY
                                      Paths to be combined with QML2_IMPORT_PATH
      --qmltestrunner-help            Pass through to get QML test runner's --help
      --qt-debug-plugins / --no-qt-debug-plugins
                                      Set QT_DEBUG_PLUGINS=1
      --test-qml-example              Test the pyqt6-tools QML example
      --help                          Show this message and exit.


--------------
Special Thanks
--------------

|MacStadium|

.. |MacStadium| image:: https://uploads-ssl.webflow.com/5ac3c046c82724970fc60918/5c019d917bba312af7553b49_MacStadium-developerlogo.png
   :alt: MacStadium
   :target: https://www.macstadium.com/

Thanks to MacStadium for providing me with a macOS system to develop and test
out the final pyqt6-tools platform.  This is still 'in work'.  See
`issue #12`_.
