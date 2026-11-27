"""Show uncaught Python exceptions in Designer in a dialog.

Otherwise they only go to stderr, which isn't visible when Designer is started
from a GUI, and PyQt aborts on some of them.
"""

import functools
import sys
import traceback

from . import import_it

QtCore = import_it('PyQt', 'QtCore')
QtWidgets = import_it('PyQt', 'QtWidgets')


def install():
    sys.excepthook = show


def show(exc_type, exc_value, exc_traceback):
    message = ''.join(
        traceback.format_exception(exc_type, exc_value, exc_traceback),
    )
    # Designer on Windows has no stderr, so sys.stderr is None.
    if sys.stderr is not None:
        sys.stderr.write(message)

    dialog(
        parent=None,
        title='Exception',
        message=message,
        icon=QtWidgets.QMessageBox.Icon.Critical,
    )


class FittedTextBrowser(QtWidgets.QTextBrowser):
    def sizeHint(self):
        default = super().sizeHint()

        if not default.isValid():
            return default

        document_size = self.document().size()
        geometry = self.screen().availableGeometry()

        if document_size.width() == 0:
            document_size.setWidth(geometry.width() * 0.25)
        if document_size.height() == 0:
            document_size.setHeight(geometry.height() * 0.4)

        scrollbar_width = QtWidgets.QApplication.style().pixelMetric(
            QtWidgets.QStyle.PixelMetric.PM_ScrollBarExtent,
        )

        width = sum((
            document_size.width(),
            self.contentsMargins().left(),
            self.contentsMargins().right(),
            scrollbar_width,
        ))

        height = sum((
            document_size.height(),
            self.contentsMargins().top(),
            self.contentsMargins().bottom(),
            scrollbar_width,
        ))

        return QtCore.QSize(int(width), int(height))


class DialogUi:
    def __init__(self, parent):
        self.layout = QtWidgets.QGridLayout(parent)
        self.icon = QtWidgets.QLabel(parent)
        self.message = FittedTextBrowser(parent)
        self.copy = QtWidgets.QPushButton(parent)
        self.buttons = QtWidgets.QDialogButtonBox(parent)

        self.copy.setText('Copy To Clipboard')

        self.layout.addWidget(self.icon, 0, 0)
        self.layout.addWidget(self.message, 0, 1, 1, 2)
        self.layout.addWidget(self.copy, 1, 1)
        self.layout.addWidget(self.buttons, 1, 2)

        self.layout.setAlignment(self.copy, QtCore.Qt.AlignmentFlag.AlignLeft)

        self.layout.setRowStretch(0, 1)
        self.layout.setColumnStretch(1, 1)


class Dialog(QtWidgets.QDialog):
    def __init__(self, *args, cancellable=False, **kwargs):
        super().__init__(*args, **kwargs)

        self.ui = DialogUi(parent=self)

        self.ui.buttons.accepted.connect(self.accept)
        self.ui.buttons.rejected.connect(self.reject)

        self.ui.copy.clicked.connect(self.copy)

        self.setLayout(self.ui.layout)
        buttons = QtWidgets.QDialogButtonBox.StandardButton.Ok
        if cancellable:
            buttons |= QtWidgets.QDialogButtonBox.StandardButton.Cancel

        self.ui.buttons.setStandardButtons(buttons)

        self.text = None
        self.html = None

        self.cached_maximum_size = self.maximumSize()

        geometry = self.screen().availableGeometry()

        self.setMaximumHeight(int(geometry.height() * 0.7))
        self.setMaximumWidth(int(geometry.width() * 0.7))

    def copy(self):
        QtWidgets.QApplication.clipboard().setText(
            self.ui.message.toPlainText() + '\n'
        )

    def set_text(self, text):
        self.ui.message.setPlainText(text)

        self.html = None
        self.text = text

        self.ui.message.setLineWrapMode(
            QtWidgets.QTextEdit.LineWrapMode.NoWrap,
        )

    def set_html(self, html):
        self.ui.message.setHtml(html)

        self.html = html
        self.text = None

        self.ui.message.setLineWrapMode(
            QtWidgets.QTextEdit.LineWrapMode.WidgetWidth,
        )

    def set_message_box_icon(self, icon):
        self.ui.icon.setPixmap(QtWidgets.QMessageBox.standardIcon(icon))

    def exec(self):
        QtCore.QTimer.singleShot(10, functools.partial(
                self.setMaximumSize,
                self.cached_maximum_size,
        ))

        return super().exec()


def dialog(parent, message, title=None, icon=None,
           rich_text=False, cancellable=False):
    box = Dialog(parent=parent, cancellable=cancellable)

    if rich_text:
        box.set_html(message)
    else:
        box.set_text(message)

    if icon is not None:
        box.set_message_box_icon(icon)

    if title is not None:
        parent_title = QtWidgets.QApplication.instance().applicationName()

        if len(parent_title) > 0:
            title = ' - '.join((
                parent_title,
                title,
            ))

        box.setWindowTitle(title)

    return box.exec()
