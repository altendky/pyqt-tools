import os
import pathlib
import sys

import setuptools
import versioneer

import _build


fspath = getattr(os, 'fspath', str)


here = pathlib.Path(__file__).parent


class InvalidVersionError(Exception):
    pass


def pad_version(v, segment_count=3):
    split = v.split('.')

    if len(split) > segment_count:
        raise InvalidVersionError('{} has more than three segments'.format(v))

    return '.'.join(split + ['0'] * (segment_count - len(split)))


# TODO: really doesn't seem quite proper here and probably should come
#       in some other way?
pyqt_version = pad_version(os.environ.setdefault('PYQT_VERSION', '6.1.0'))
qt_version = pad_version(os.environ.setdefault('QT_VERSION', '6.1.0'))
qt_major_version = qt_version.partition('.')[0]

pyqt_plugins_wrapper_version = versioneer.get_versions()['version']
pyqt_plugins_version = '{}.{}'.format(
    pyqt_version,
    pyqt_plugins_wrapper_version,
)

# Inclusive of the lower bound and exclusive of the upper
qt_tools_wrapper_range = ['1.2', '2']

qt_tools_version_format = '>={qt}.{wrapper[0]}, <{qt}.{wrapper[1]}'
qt_tools_version_specifier = qt_tools_version_format.format(
    qt=qt_version,
    wrapper=qt_tools_wrapper_range,
)


with open('README.rst') as f:
    readme = f.read()

if qt_major_version == '5':
    replacements = [
        ["qt6", "qt5"],
        ["Qt6", "Qt5"],
        ["Qt6", "Qt 5"],
        ["6.4", "5.15"],
    ]
    for a, b in replacements:
        readme = readme.replace(a, b)


class Dist(setuptools.Distribution):
    def has_ext_modules(self):
        # Event if we don't have extension modules (e.g. on PyPy) we want to
        # claim that we do so that wheels get properly tagged as Python
        # specific.  (thanks dstufft!)
        return True


distribution_name = "pyqt{}-plugins".format(qt_major_version)
import_name = distribution_name.replace('-', '_')


setuptools.setup(
    name=distribution_name,
    description="PyQt Designer and QML plugins",
    long_description=readme,
    long_description_content_type='text/x-rst',
    url='https://github.com/altendky/pyqt-tools',
    author="Kyle Altendorf",
    author_email='sda@fstab.net',
    license='GPLv3',
    classifiers=[
        # complete classifier list: https://pypi.org/pypi?%3Aaction=list_classifiers
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        'Operating System :: POSIX :: Linux',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Programming Language :: Python :: 3.14',
        # PyQt5 doesn't build on Python 3.15.
        *(['Programming Language :: Python :: 3.15'] if qt_major_version != '5' else []),
        'Topic :: Software Development',
        'Topic :: Utilities',
    ],
    cmdclass={'build_py': _build.BuildPy},
    distclass=Dist,
    packages=[package.replace('pyqt_plugins', import_name) for package in setuptools.find_packages('src')],
    package_dir={import_name: 'src/pyqt_plugins'},
    version=pyqt_plugins_version,
    include_package_data=True,
    python_requires=">=3.11",
    install_requires=[
        'click',
        'pyqt{}=={}'.format(qt_major_version, pyqt_version),
        'pyqt{}-qt{}=={}'.format(qt_major_version, qt_major_version, qt_version),
        'qt{}-tools{}'.format(
            qt_major_version,
            qt_tools_version_specifier,
        ),
    ],
)
