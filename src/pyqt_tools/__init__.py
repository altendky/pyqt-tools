from ._version import get_versions
__version__ = get_versions()['version']
del get_versions


# TODO: CAMPid 0970432108721340872130742130870874321
import pkg_resources
string_version = pkg_resources.get_distribution(__name__.partition('.')[0]).version
version = tuple(
    int(segment)
    for segment in string_version.split('.')[:3]
)
major = version[0]


def _import_it(*segments):
    import importlib

    m = {
        "pyqt_tools": "pyqt{major}_tools".format(major=major),
        "pyqt_plugins": "pyqt{major}_plugins".format(major=major),
        "qt_tools": "qt{major}_tools".format(major=major),
        "qt_applications": "qt{major}_applications".format(major=major),
        "PyQt": "PyQt{major}".format(major=major),
    }

    majored = [m[segments[0]], *segments[1:]]
    return importlib.import_module(".".join(majored))
