import pathlib


# TODO: CAMPid 0970432108721340872130742130870874321
def import_it(*segments):
    import importlib
    import pkg_resources

    major = int(pkg_resources.get_distribution(__name__).version.partition(".")[0])

    m = {
        "pyqt_tools": "pyqt{major}_tools".format(major=major),
        "pyqt_plugins": "pyqt{major}_plugins".format(major=major),
        "qt_tools": "qt{major}_tools".format(major=major),
        "qt_applications": "qt{major}_applications".format(major=major),
    }

    majored = [m[segments[0]], *segments[1:]]
    return importlib.import_module(".".join(majored))


qt_applications = import_it("qt_applications")
import_it("qt_applications", "_applications")


from ._version import get_versions
__version__ = get_versions()['version']
del get_versions


_root = pathlib.Path(__file__).absolute().parent
_bin = _root.joinpath('Qt', 'bin')
_plugins = _root.joinpath('Qt', 'plugins')


def _application_names():
    return [*qt_applications._applications.application_paths.keys()]


def _application_path(name):
    return _bin.joinpath(qt_applications._applications.application_paths[name])
