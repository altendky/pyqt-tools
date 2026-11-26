from PyQt5 import QtDesigner


class RedPlugin(QtDesigner.QPyDesignerCustomWidgetPlugin):
    # https://wiki.python.org/moin/PyQt/Using_Python_Custom_Widgets_in_Qt_Designer

    def __init__(self):
        raise Exception('This exception is being intentionally raised to demonstrate the pyqt5-tools exception dialog.')
