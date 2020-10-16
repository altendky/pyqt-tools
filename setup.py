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
import vcversioner

try:
    import wheel.bdist_wheel
except ImportError:
    wheel = None


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


version = vcversioner.find_version(
        version_module_paths=['_version.py'],
        vcs_args=['git', '--git-dir', '%(root)s/.git', 'describe',
                     '--tags', '--long', '--abbrev=999'],
    )

def pad_version(v):
    split = v.split('.')
    return '.'.join(split + ['0'] * (3 - len(split)))

# TODO: really doesn't seem quite proper here and probably should come
#       in some other way?
os.environ.setdefault('QT_VERSION', '5.15.1')

version = '.'.join((
    pad_version(os.environ['QT_VERSION']),
    version.version,
))


with open('README.rst') as f:
    readme = f.read()


class Dist(setuptools.Distribution):
    def has_ext_modules(self):
        # Event if we don't have extension modules (e.g. on PyPy) we want to
        # claim that we do so that wheels get properly tagged as Python
        # specific.  (thanks dstufft!)
        return True


setuptools.setup(
    name="qt-tools",
    description="The collection of Qt tools easily installable in Python",
    long_description=readme,
    long_description_content_type='text/x-rst',
    url='https://github.com/altendky/qt-tools',
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
    cmdclass={
        'bdist_wheel': BdistWheel,
        'build_py': build.BuildPy,
    },
    distclass=Dist,
    packages=setuptools.find_packages('src'),
    package_dir={'': 'src'},
    version=version,
    include_package_data=True,
    python_requires=">=3.5",
    install_requires=[
        'click',
        'python-dotenv',
    ],
)
