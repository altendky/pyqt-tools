import click

import pyqt5toolsbuild.utils


@click.group()
def cli():
    pass


@cli.command()
@click.option('--version')
@click.option('--levels', type=int)
@click.option('--remove-dots', default=False)
def exact(version, levels, remove_dots):
    version = pyqt5toolsbuild.utils.Version.from_string(version)

    s = version.exactly(levels=levels)

    if remove_dots:
        s.replace('.', '')

    print(s)


@cli.command()
@click.option('--version')
def qt(version):
    version = pyqt5toolsbuild.utils.Version.from_string(version)

    print(pyqt5toolsbuild.utils.pyqt_to_qt_version(version))
