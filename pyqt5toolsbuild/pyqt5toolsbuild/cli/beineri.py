import click

import pyqt5toolsbuild.utils


@click.group()
def cli():
    pass


@cli.command()
@click.option('--version')
def ppa(version):
    f = 'ppa:beineri/opt-qt{}-trusty'
    version = pyqt5toolsbuild.utils.Version.from_string(version)
    print(f.format(str(version.stripped()).replace('.', '')))
