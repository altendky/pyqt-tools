===========
pyqt5-tools
===========


|PyPI| |Pythons| |GitHub|

The PyQt5 wheels do not provide tools such as Qt Designer that were included in
the old binary installers. This package aims to provide those in a separate
package which is useful for developers while the official PyQt5 wheels stay
focused on fulfilling the dependencies of PyQt5 applications.

Both Windows and Linux are supported.  Adjust paths etc accordingly if applying
the explanations below in Linux rather than Windows.  macOS support is
incomplete but see `issue #12`_ if you want to discuss it.

.. |PyPI| image:: https://img.shields.io/pypi/v/pyqt5-tools.svg
   :alt: PyPI version
   :target: https://pypi.org/project/pyqt5-tools/

.. |Pythons| image:: https://img.shields.io/pypi/pyversions/pyqt5-tools.svg
   :alt: supported Python versions
   :target: https://pypi.org/project/pyqt5-tools/

.. |GitHub| image:: https://img.shields.io/github/last-commit/altendky/pyqt5-tools/master.svg
   :alt: source on GitHub
   :target: https://github.com/altendky/pyqt5-tools

.. _`issue #12`: https://github.com/altendky/pyqt5-tools/issues/12

------------
Installation
------------

.. code-block:: powershell

  yourenv/Scripts/pip.exe install pyqt5-tools~=5.15

You will generally install pyqt5-tools using ``pip install``.  In most cases
you should be using virtualenv_ or venv_ to create isolated environments to
install your dependencies in.  The above command assumes an env in the
directory ``yourenv``.  The ``~=5.15`` specifies a `release compatible with`_
5.11 which will be the latest version of pyqt5-tools built for PyQt5_ 5.11. If
you are using a different PyQt5 version, specify it instead of 5.11.  PyPI
keeps a list of `all available versions`_.

.. _virtualenv: https://virtualenv.pypa.io/en/stable/
.. _venv: https://docs.python.org/3/library/venv.html
.. _PyQt5: https://pypi.org/project/PyQt5/
.. _`release compatible with`: https://www.python.org/dev/peps/pep-0440/#compatible-release
.. _`all available versions`: https://pypi.org/project/pyqt5-tools/#history

Note:
    As of pyqt5-tools v2 the package has been broken down into three pieces.
    The wrappers remain here but the plugins are located in pyqt5-plugins_ and
    the applications are in qt5-applications_.

.. _pyqt5-plugins: https://github.com/altendky/pyqt-plugins
.. _qt5-applications: https://github.com/altendky/qt-applications

-----
Usage
-----

For each tool a script is created such that you get files like
``Scripts/designer.exe`` to launch the programs.  Each one searches up the
filesystem tree from your current working directory to find a ``.env`` file
and loads it if found.  If found the environment variable
``DOT_ENV_DIRECTORY`` will be set to the directory containing the ``.env``
file.  With this extra variable you can specify paths relative to the
``.env`` location.

.. code-block:: powershell

  PYQTDESIGNERPATH=${PYQTDESIGNERPATH};${DOT_ENV_DIRECTORY}/path/to/my/widgets

Additionally, each ``pyqt5*`` wrapper listed below includes a parameter to
run a basic example which can be used to see if the plugins are working.
These examples are `not` intended to be used as examples of good code.

Designer
========

There is a ``Scripts/pyqt5designer.exe`` entry point that will help fill out
``PYQTDESIGNERPATH`` from either command line arguments or a ``.env`` file.
Unknown arguments are passed through to the original Qt Designer program.

.. code-block::

    Usage: pyqt5designer [OPTIONS]

    Options:
      -p, --widget-path DIRECTORY     Paths to be combined with PYQTDESIGNERPATH
      --example-widget-path           Include the path for the pyqt5-tools example
                                      button (c:/users/sda/testenv/lib/site-
                                      packages/pyqt5_tools)
      --designer-help                 Pass through to get Designer's --help
      --test-exception-dialog         Raise an exception to check the exception
                                      dialog functionality.
      --qt-debug-plugins / --no-qt-debug-plugins
                                      Set QT_DEBUG_PLUGINS=1
      --help                          Show this message and exit.

If you want to use ``Form`` > ``View Code...`` from within Designer you can
run ``Scripts/pyqt5toolsinstalluic.exe`` and it will copy ``pyuic5.exe``
such that Designer will use it and show you generated Python code.  ``pyqt5``
must already be installed or this script will be unable to find the original
``pyuic5.exe`` to copy.

In addition to the standard features of the official Designer plugin, this
provides an exception dialog for your widget's Python code.  Otherwise Designer
in Windows silently crashes on Python exceptions.

QML Plugin
==========

The QML plugin is also included.  In the future a tool may be provided to
handle copying of the plugin to each directory where it is needed.  For now
this must be done manually.

``site-packages/pyqt5_tools/Qt/bin/plugins/pyqt5qmlplugin.dll``

QML Scene
=========

.. code-block::

    Usage: pyqt5qmlscene [OPTIONS]

    Options:
      -p, --qml2-import-path DIRECTORY
                                      Paths to be combined with QML2_IMPORT_PATH
      --qmlscene-help                 Pass through to get QML scene's --help
      --qt-debug-plugins / --no-qt-debug-plugins
                                      Set QT_DEBUG_PLUGINS=1
      --run-qml-example               Run the pyqt5-tools QML example
      --help                          Show this message and exit.

QML Test Runner
===============

.. code-block::

    Usage: pyqt5qmltestrunner [OPTIONS]

    Options:
      -p, --qml2-import-path DIRECTORY
                                      Paths to be combined with QML2_IMPORT_PATH
      --qmltestrunner-help            Pass through to get QML test runner's --help
      --qt-debug-plugins / --no-qt-debug-plugins
                                      Set QT_DEBUG_PLUGINS=1
      --test-qml-example              Test the pyqt5-tools QML example
      --help                          Show this message and exit.


--------------
Special Thanks
--------------

|MacStadium|

.. |MacStadium| image:: https://uploads-ssl.webflow.com/5ac3c046c82724970fc60918/5c019d917bba312af7553b49_MacStadium-developerlogo.png
   :alt: MacStadium
   :target: https://www.macstadium.com/

Thanks to MacStadium for providing me with a macOS system to develop and test out the final pyqt5-tools platform.
