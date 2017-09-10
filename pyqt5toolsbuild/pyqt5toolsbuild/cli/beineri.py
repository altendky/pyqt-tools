import click

import pyqt5toolsbuild.util


@click.group
def cli():
    pass


@cli.command
@click.option('--version')
def ppa(version):
    f = 'ppa:beineri/opt-qt{}-trusty'
    version = pyqt5toolsbuild.util.Version.from_string(version)
    print(f.format(version.strip().replace('.', '')))
