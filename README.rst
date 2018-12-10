pyqt5-tools
===========

|AppVeyor|_

The PyQt5 wheels do not provide tools such as Qt Designer that were included in
the old binary installers. This package aims to provide those in a separate
package which is useful for developers while the official PyQt5 wheels stay
focused on fulfilling the dependencies of PyQt5 applications.

Installation
------------

.. code-block:: powershell

  yourenv\Scripts\pip.exe install --pre pyqt5-tools~=5.11

You will generally install pyqt5-tools using ``pip install``.
In most cases you should be using virtualenv_ or venv_ to create isolated environments to install your dependencies in.
The above command assumes an env in the directory ``yourenv``.
The ``--pre`` allows for the latest version to be installed despite not being a full release version.
You will  have to decide if this is a good option for you at any given point in time.
The ``~=5.11`` specifies a `release compatible with`_ 5.11 which will be the latest version of pqyt5-tools built for PyQt5_ 5.11.
If you are using a different PyQt5 version, specify it instead of 5.11.
PyPI keeps a list of `all available versions`_.

.. _virtualenv: https://virtualenv.pypa.io/en/stable/
.. _venv: https://docs.python.org/3/library/venv.html
.. _PyQt5: blue
.. _`release compatible with`: https://www.python.org/dev/peps/pep-0440/#compatible-release
.. _`all available versions`: https://pypi.org/project/pyqt5-tools/#history

Usage
-----

For each tool a script is created such that you get files like
``Scripts\designer.exe`` to launch the programs.  Each one searches up the
filesystem tree to find a ``.env`` file and loads it if found.  If found
the environment variable ``DOT_ENV_DIRECTORY`` will be set to the directory
containing the ``.env`` file.  With this extra variable you can specify paths
relative to the ``.env`` location.

.. code-block:: powershell

  PYQTDESIGNERPATH=${PYQTDESIGNERPATH};${DOT_ENV_DIRECTORY}/path/to/my/widgets

There is a ``Scripts\pyqt5designer.exe`` entry point that will help fill out
``PYQTDESIGNERPATH`` from either command line arguments or a ``.env`` file.
Unknown arguments are passed through to the original Qt Designer program.

.. code-block::

  Usage: pyqt5designer [OPTIONS]

  Options:
    -p, --widget-path DIRECTORY  Paths to be combined with PYQTDESIGNERPATH
    --example-widget-path        Include the path for the pyqt5-tools example
                                 button (c:\users\sda\desktop\venv64\lib\site-
                                 packages\pyqt5_tools)
    --designer-help              Pass through to get Designer's --help
    --test-exception-dialog      Raise an exception to check the exception
                                 dialog functionality.
    --help                       Show this message and exit.

If you want to use ``Form`` > ``View Code...`` from within Designer you can
run ``Scripts\pyqt5toolsinstalluic.exe`` and it will copy ``pyuic5.exe``
such that Designer will use it and show you generated Python code.  ``pyqt5``
must already be installed or this script will be unable to find the original
``pyuic5.exe`` to copy.

In addition to the standard features of the official Designer plugin, this
provides an exception dialog for your widget's Python code.  Otherwise Designer
in Windows silently crashes on Python exceptions.

The QML plugin is also included for use with ``qmlscene.exe`` and
``qmltestrunner.exe``.

.. |AppVeyor| image:: https://ci.appveyor.com/api/projects/status/g95n2ri0e479uvoe?svg=true
   :alt: AppVeyor build status
.. _AppVeyor: https://ci.appveyor.com/project/KyleAltendorf/pyqt5-tools
