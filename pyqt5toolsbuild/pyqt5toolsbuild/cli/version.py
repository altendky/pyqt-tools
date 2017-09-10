import click

import pyqt5toolsbuild.utils


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
    version = pyqt5toolsbuild.utils.Version.from_string(version)

    print(pyqt5toolsbuild.utils.pyqt_to_qt_version(version))
