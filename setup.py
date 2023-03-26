import os

import setuptools
import versioneer


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
pyqt_major_version = pyqt_version.partition('.')[0]


pyqt_tools_wrapper_version = versioneer.get_versions()['version']
pyqt_tools_version = '{}.{}'.format(pyqt_version, pyqt_tools_wrapper_version)


# Inclusive of the lower bound and exclusive of the upper
pyqt_plugins_wrapper_range = ['2.2', '3']

# Must be False for release.  PyPI won't let you upload with a URL dependency.
use_pyqt_plugins_url = True

if use_pyqt_plugins_url:
    pyqt_plugins_url = ' @ git+https://github.com/altendky/pyqt-plugins@maybe'
    pyqt_plugins_version_specifier = ''
else:
    pyqt_plugins_url = ''
    pyqt_plugins_version_format = '>={pyqt}.{wrapper[0]}, <{pyqt}.{wrapper[1]}'
    pyqt_plugins_version_specifier = pyqt_plugins_version_format.format(
        pyqt=pyqt_version,
        wrapper=pyqt_plugins_wrapper_range,
    )


with open('README.rst') as f:
    readme = f.read()


distribution_name = "pyqt{}-tools".format(pyqt_major_version)
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
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Topic :: Software Development',
        'Topic :: Utilities',
    ],
    packages=[package.replace('pyqt_tools', import_name) for package in setuptools.find_packages('src')],
    package_dir={import_name: 'src/pyqt_tools'},
    version=pyqt_tools_version,
    include_package_data=True,
    python_requires=">=3.7",
    install_requires=[
        'click',
        'pyqt{}=={}'.format(pyqt_major_version, pyqt_version),
        'pyqt{}-plugins{}{}'.format(
            pyqt_major_version,
            pyqt_plugins_version_specifier,
            pyqt_plugins_url,
        ),
        'python-dotenv',
    ],
    entry_points={
        'console_scripts': [
            'pyqt{major}-tools = pyqt{major}_tools.entrypoints:main'.format(major=pyqt_major_version),
        ]
    }
)
