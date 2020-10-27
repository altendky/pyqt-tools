import os

import setuptools
import versioneer


# TODO: really doesn't seem quite proper here and probably should come
#       in some other way?
os.environ.setdefault('PYQT_VERSION', '5.15.1')
os.environ.setdefault('QT_VERSION', '5.15.1')


def pad_version(v):
    split = v.split('.')
    return '.'.join(split + ['0'] * (3 - len(split)))


def calculate_version():
    version = versioneer.get_versions()['version']

    version = '.'.join((
        pad_version(os.environ['PYQT_VERSION']),
        version,
    ))

    return version


setuptools.setup(
    version=calculate_version(),
)
