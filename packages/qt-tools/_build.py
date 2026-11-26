import faulthandler
faulthandler.enable()

import os
import pathlib
import sys
import tempfile
import textwrap
import traceback
import typing

import attr
import setuptools.command.build_py


# TODO: CAMPid 0970432108721340872130742130870874321
def import_it(*segments):
    import importlib

    version = os.environ['QT_VERSION']
    major = version.partition('.')[0]

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


class BuildPy(setuptools.command.build_py.build_py):
    def build_packages(self):
        super().build_packages()

        try:
            [package_name] = (
                package
                for package in self.distribution.packages
                if '.' not in package
            )

            build_command = self.distribution.command_obj['build']

            cwd = pathlib.Path.cwd()
            lib_path = cwd / build_command.build_lib
            package_path = lib_path / package_name

            build(package_path=package_path)

            if getattr(self.distribution, 'entry_points', None) is None:
                self.distribution.entry_points = {}
        except:
            # something apparently consumes tracebacks (not exception messages)
            # for OSError at least.  let's avoid that silliness.
            traceback.print_exc()
            raise


def checkpoint(name):
    print('    ----<==== {} ====>----'.format(name))


def build(package_path: pathlib.Path):
    applications = [
        Application(name=name, path=qt_applications._application_path(name))
        for name in qt_applications._application_names()
    ]

    checkpoint('Write Entry Points')
    entry_points_py = package_path.joinpath('entrypoints.py')

    write_subcommands(
        entry_points_py=entry_points_py,
        applications=applications,
    )


def create_script_function_name(path: pathlib.Path):
    return path.stem.replace('-', '_')


@attr.s
class Application:
    name = attr.ib()
    path = attr.ib()


subcommand_template = """
@main.command(
    add_help_option=False,
    context_settings={{
        'ignore_unknown_options': True,
        'allow_extra_args': True,
    }},
)
@click.pass_context
def {function_name}(ctx):
    return run({application_name!r}, args=ctx.args)
"""


def write_subcommands(
        entry_points_py: pathlib.Path,
        applications: typing.List[Application],
) -> None:
    with entry_points_py.open('a', encoding='utf-8', newline='\n') as f:
        f.write(textwrap.dedent('''\
        
            # ----  start of generated wrapper entry points
        
        '''))

        for application in sorted(applications, key=lambda a: a.name):
            function_name = create_script_function_name(application.path)
            stem = application.path.stem.casefold()

            subcommand_source = subcommand_template.format(
                function_name=function_name,
                application_name=stem,
            )

            f.write(subcommand_source + '\n')

        f.write(textwrap.dedent('''\

            # ----  end of generated wrapper subcommands

        '''))
