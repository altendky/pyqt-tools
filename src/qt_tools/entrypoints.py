import os
import pathlib
import subprocess
import sys
import sysconfig

import dotenv


fspath = getattr(os, 'fspath', str)


here = pathlib.Path(__file__).parent
bin = here/'Qt'/'bin'

maybe_extension = {
    'linux': lambda name: name,
    'win32': lambda name: '{}.exe'.format(name),
    'darwin': lambda name: name,
}[sys.platform]


def load_dotenv():
    env_path = dotenv.find_dotenv(usecwd=True)
    if len(env_path) > 0:
        os.environ['DOT_ENV_DIRECTORY'] = str(pathlib.Path(env_path).parent)
        os.environ['SITE_PACKAGES'] = sysconfig.get_path('platlib')
        dotenv.load_dotenv(dotenv_path=env_path, override=True)


def create_env(reference):
    # TODO: uck, mutating
    load_dotenv()

    env = dict(reference)

    # env.update(add_to_env_var_path_list(
    #     env=env,
    #     name='QT_PLUGIN_PATH',
    #     before=[],
    #     after=[fspath(here / 'Qt' / 'plugins')],
    # ))

    if sys.platform == 'linux':
        env.update(add_to_env_var_path_list(
            env=env,
            name='LD_LIBRARY_PATH',
            before=[''],
            after=[sysconfig.get_config_var('LIBDIR')],
        ))

    return env


def add_to_env_var_path_list(env, name, before, after):
    return {
        name: os.pathsep.join((
            *before,
            env.get(name, ''),
            *after
        ))
    }


# def designer():
#     env = create_env(os.environ)
#     return subprocess.call(
#         [
#             str(here/'Qt'/'bin'/'designer.exe'),
#             *sys.argv[1:],
#         ],
#         env=env,
#     )
