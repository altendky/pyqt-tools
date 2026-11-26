"""Record the exception dialog for tests, then close it.

Put this directory in PYQTDESIGNERPATH after the excepthook plugin directory
and before the plugins whose exceptions should be recorded.
"""

import functools
import json
import os
import pathlib
import sys

from ... import exceptiondialog
from ... import import_it

QtCore = import_it('PyQt', 'QtCore')
QtWidgets = import_it('PyQt', 'QtWidgets')

test_path_env_var = 'PYQT_PLUGINS_EXCEPTION_DIALOG_TEST_PATH'


def install():
    path = pathlib.Path(os.environ[test_path_env_var])
    hook = sys.excepthook

    def capture(*args):
        QtCore.QTimer.singleShot(0, functools.partial(record, path=path, hook=hook))
        hook(*args)

    sys.excepthook = capture


def record(path, hook, attempts=100):
    dialog = QtWidgets.QApplication.activeModalWidget()

    # Designer has modal dialogs of its own, such as New Form.
    if not isinstance(dialog, exceptiondialog.Dialog):
        if attempts > 0:
            QtCore.QTimer.singleShot(100, functools.partial(
                record,
                path=path,
                hook=hook,
                attempts=attempts - 1,
            ))
        return

    text = dialog.ui.message.toPlainText()
    path.write_text(json.dumps({
        'hook': '{}.{}'.format(hook.__module__, hook.__qualname__),
        'text': text,
    }))
    dialog.accept()
