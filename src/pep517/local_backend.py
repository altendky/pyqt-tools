import os

import setuptools.build_meta
import versioneer


build_wheel = setuptools.build_meta.build_wheel
build_sdist = setuptools.build_meta.build_sdist
prepare_metadata_for_build_wheel = (
    setuptools.build_meta.prepare_metadata_for_build_wheel
)
get_requires_for_build_sdist = (
    setuptools.build_meta.get_requires_for_build_sdist
)
get_requires_for_build_wheel = (
    setuptools.build_meta.get_requires_for_build_wheel
)


# # TODO: really doesn't seem quite proper here and probably should come
# #       in some other way?
# os.environ.setdefault('PYQT_VERSION', '5.15.1')
# os.environ.setdefault('QT_VERSION', '5.15.1')
#
#
# def pad_version(v):
#     split = v.split('.')
#     return '.'.join(split + ['0'] * (3 - len(split)))
#
#
# def calculate_version():
#     version = versioneer.get_versions()['version']
#
#     version = '.'.join((
#         pad_version(os.environ['PYQT_VERSION']),
#         version,
#     ))
#
#     return version


# version = calculate_version()
# pyqt_version = os.environ['PYQT_VERSION']
# qt_version = os.environ['QT_VERSION']
#
# install_requires = [
#     'click',
#     'pyqt5=={}'.format(os.environ['PYQT_VERSION']),
#     'pyqtplugins @ git+https://github.com/altendky/pyqt5-tools@just_plugins',
#     'qttools @ git+https://github.com/altendky/pyqt5-tools@just_applications',
# ],
