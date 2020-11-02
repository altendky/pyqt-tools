import os
import pathlib
import sys
import sysconfig


from ._version import get_versions
__version__ = get_versions()['version']
del get_versions

root = pathlib.Path(__file__).parent
bin = root.joinpath('Qt', 'bin')

_application_filters = {
    'linux': lambda path: True,
    'win32': lambda path: path.suffix == '.exe'
}
_application_filter = _application_filters[sys.platform]

_applications = {
    path.stem: path
    for path in bin.iterdir()
    if _application_filter(path=path)
}


def application_path(name):
    return _applications[name]


def add_to_env_var_path_list(environment, name, before, after):
    return {
        name: os.pathsep.join((
            *before,
            environment.get(name, ''),
            *after
        ))
    }


def create_environment(reference):
    environment = dict(reference)

    if sys.platform == 'linux':
        environment.update(add_to_env_var_path_list(
            environment=environment,
            name='LD_LIBRARY_PATH',
            before=[''],
            after=[sysconfig.get_config_var('LIBDIR')],
        ))

    return environment
