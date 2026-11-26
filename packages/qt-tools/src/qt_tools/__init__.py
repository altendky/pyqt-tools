import os
import sys
import sysconfig


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


fspath = getattr(os, 'fspath', str)


from ._version import get_versions
__version__ = get_versions()['version']
del get_versions


def bin_path():
    return qt_applications._bin


def application_names():
    return qt_applications._application_names()


def application_path(name):
    return qt_applications._application_path(name)


def _add_to_env_var_path_list(environment, name, before, after):
    return {
        name: os.pathsep.join((
            *before,
            environment.get(name, ''),
            *after
        ))
    }


def create_environment(reference=None):
    if reference is None:
        reference = os.environ

    environment = dict(reference)

    if sys.platform in ['linux', 'darwin']:
        environment.update(_add_to_env_var_path_list(
            environment=environment,
            name='LD_LIBRARY_PATH',
            before=[''],
            after=[sysconfig.get_config_var('LIBDIR')],
        ))
    if sys.platform == 'win32':
        environment.update(_add_to_env_var_path_list(
            environment=environment,
            name='PATH',
            before=[''],
            after=[sysconfig.get_path('scripts')],
        ))

    return environment


def create_command_elements(name, sys_platform=sys.platform):
    path = application_path(name)

    if sys_platform == 'darwin' and path.suffix == '.app':
        inner = path.joinpath('Contents', 'MacOS', path.stem)
        return [fspath(inner)]

    return [fspath(path)]
