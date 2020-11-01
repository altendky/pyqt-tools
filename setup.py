import os
import pathlib
import sys

here = pathlib.Path(__file__).parent

sys.path.insert(0, os.fspath(here))
# TODO: yuck, put the build command in a separate project and
#       build-requires it?
import build
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
            python, abi, plat = super().get_tag()
            python = 'py3'
            abi = 'none'
            return python, abi, plat


def pad_version(v, segment_count=3):
    split = v.split('.')
    if len(split) > segment_count:
        raise InvalidVersionError('{} has more than three segments'.format(v))

    return '.'.join(split + ['0'] * (segment_count - len(split)))


# TODO: really doesn't seem quite proper here and probably should come
#       in some other way?
qt_version = pad_version(os.environ.setdefault('QT_VERSION', '5.15.1'))


qt5_applications_wrapper_version = pad_version(versioneer.get_versions()['version'])
qt5_applications_version = '{}.{}'.format(qt_version, qt5_applications_wrapper_version)


with open('README.rst') as f:
    readme = f.read()


class Dist(setuptools.Distribution):
    def has_ext_modules(self):
        # Event if we don't have extension modules (e.g. on PyPy) we want to
        # claim that we do so that wheels get properly tagged as Python
        # specific.  (thanks dstufft!)
        return True


cmdclass['build_py'] = build.create_build_py(cmdclass=cmdclass['build_py'])
cmdclass['bdist_wheel'] = BdistWheel


setuptools.setup(
    name="qt5-applications",
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
        'Operating System :: Microsoft :: Windows',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Topic :: Software Development',
        'Topic :: Utilities',
    ],
    distclass=Dist,
    packages=setuptools.find_packages('src'),
    package_dir={'': 'src'},
    version=qt5_applications_version,
    include_package_data=True,
    python_requires=">=3.5",
)
