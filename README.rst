pyqt5-tools
===========

|AppVeyor|_

The PyQt5 wheels do not provide tools such as Qt Designer that were included in
the old binary installers. This package aims to provide those in a separate
package which is useful for developers while the official PyQt5 wheels stay
focused on fulfilling the dependencies of PyQt5 applications.

For each tool a script is created such that you get files like
``Scripts\designer.exe`` to launch the programs.

There is a ``Scripts\pyqt5designer.exe`` entry point that will help fill out
``PYQTDESIGNERPATH`` from either command line arguments or a ``.env`` file.
Unknown arguments are passed through to the original Qt Designer program.

.. code-block::

  Usage: pyqt5designer [OPTIONS]

  Options:
    -p, --widget-path DIRECTORY  Paths to be combined with PYQTDESIGNERPATH
    --designer-help              Pass through to get Designer's --help
    --help                       Show this message and exit.

If you want to use ``Form`` > ``View Code...`` from within Designer you can
run ``Scripts\pyqt5toolsinstalluic.exe`` and it will copy ``pyuic5.exe``
such that Designer will use it and show you generated Python code.  ``pyqt5``
must already be installed or this script will be unable to find the original
``pyuic5.exe`` to copy.

In addition to the standard features of the official Designer plugin, this
provides an exception dialog for your widget's Python code.  Otherwise Designer
in Windows silently crashes on Python exceptions.

.. |AppVeyor| image:: https://ci.appveyor.com/api/projects/status/g95n2ri0e479uvoe?svg=true
   :alt: AppVeyor build status
.. _AppVeyor: https://ci.appveyor.com/project/KyleAltendorf/pyqt5-tools
