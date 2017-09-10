import click

import pyqt5toolsbuild.util


@click.group
def cli():
    pass


@cli.command
@click.option('--version')
@click.option('--levels', type=int)
def exact(version, levels):
    version = pyqt5toolsbuild.utilVersion.from_string(version)

    print(version.exactly(levels=levels))


@cli.command
@click.option('--version')
def qt(version):
    version = pyqt5toolsbuild.util.Version.from_string(version)

    print(pyqt5toolsbuild.util.pyqt_to_qt_version(version))
