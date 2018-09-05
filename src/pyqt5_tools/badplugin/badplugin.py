from PyQt5 import QtDesigner


class BadPlugin(QtDesigner.QPyDesignerCustomWidgetPlugin):
    # https://wiki.python.org/moin/PyQt/Using_Python_Custom_Widgets_in_Qt_Designer

    def __init__(self, parent=None):
        raise Exception('hopefully you see this in a nice dialog')
