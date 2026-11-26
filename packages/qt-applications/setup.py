import itertools
import os
import pathlib
import sys

here = pathlib.Path(__file__).parent


fspath = getattr(os, 'fspath', str)


sys.path.insert(0, fspath(here))
# TODO: yuck, put the _build command in a separate project and
#       _build-requires it?
import _build
sys.path.pop(0)

import setuptools
import versioneer

try:
    import wheel.bdist_wheel
except ImportError:
    wheel = None


class InvalidVersionError(Exception):
    pass


if wheel is None:
    BdistWheel = None
else:
    class BdistWheel(wheel.bdist_wheel.bdist_wheel):
        def finalize_options(self):
            super().finalize_options()
            # Mark us as not a pure python package
            self.root_is_pure = False

        def get_tag(self):
            python, abi, _ = super().get_tag()
            python = 'py3'
            abi = 'none'
            if sys.platform == 'linux':
                plat = 'manylinux_2_17_x86_64'
            elif sys.platform == 'darwin':
                if qt_major_version == '5':
                    plat = 'macosx_10_14_x86_64'
                elif qt_major_version == '6':
                    plat = 'macosx_10_14_universal2'
            elif sys.platform == 'win32':
                if sys.maxsize <= 2**32:
                    plat = 'win32'
                else:
                    plat = 'win_amd64'
            return python, abi, plat


def pad_version(v, segment_count=3):
    split = v.split('.')

    if len(split) > segment_count:
        raise InvalidVersionError('{} has more than three segments'.format(v))

    return '.'.join(split + ['0'] * (segment_count - len(split)))


# TODO: really doesn't seem quite proper here and probably should come
#       in some other way?
qt_version = pad_version(os.environ.setdefault('QT_VERSION', '6.1.0'))
qt_major_version = qt_version.partition('.')[0]

qt_applications_wrapper_version = versioneer.get_versions()['version']
qt_applications_version = '{}.{}'.format(qt_version, qt_applications_wrapper_version)


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


distribution_name = "qt{}-applications".format(qt_major_version)
import_name = distribution_name.replace('-', '_')


setuptools.setup(
    name=distribution_name,
    description="The collection of Qt tools easily installable in Python",
    long_description=readme,
    long_description_content_type='text/x-rst',
    url='https://github.com/altendky/qt-applications',
    author="Kyle Altendorf",
    author_email='sda@fstab.net',
    license='LGPLv3',
    classifiers=[
        # complete classifier list: https://pypi.org/pypi?%3Aaction=list_classifiers
        'Development Status :: 4 - Beta',
        'Environment :: Win32 (MS Windows)',
        'Intended Audience :: Developers',
        "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",
        'Operating System :: POSIX :: Linux',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Topic :: Software Development',
        'Topic :: Utilities',
    ],
    install_requires=[
        # TODO: forcing since we use pkg_resources, though we should stop using that as it is deprecated
        "setuptools",
    ],
    cmdclass={'bdist_wheel': BdistWheel, 'build_py': _build.BuildPy},
    distclass=Dist,
    packages=[package.replace('qt_applications', import_name) for package in setuptools.find_packages('src')],
    package_dir={import_name: 'src/qt_applications'},
    version=qt_applications_version,
    include_package_data=True,
    python_requires=">=3.9",
)
