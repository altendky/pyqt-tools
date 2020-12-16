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
pyqt_version = pad_version(os.environ.setdefault('PYQT_VERSION', '5.15.1'))
qt_version = pad_version(os.environ.setdefault('QT_VERSION', '5.15.1'))
pyqt_major_version = pyqt_version.partition('.')[0]


pyqt5_tools_wrapper_version = '3'
pyqt5_tools_version = '{}.{}'.format(pyqt_version, pyqt5_tools_wrapper_version)


# Inclusive of the lower bound and exclusive of the upper
pyqt_plugins_wrapper_range = ['2', '3']

# Must be False for release.  PyPI won't let you upload with a URL dependency.
use_pyqt_plugins_url = False

if use_pyqt_plugins_url:
    pyqt_plugins_url = ' @ git+https://github.com/altendky/pyqt-plugins@qt-tools'
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


setuptools.setup(
    name="pyqt5_tools",
    description="PyQt Designer and QML plugins",
    long_description=readme,
    long_description_content_type='text/x-rst',
    url='https://github.com/altendky/pyqt5-tools',
    author="Kyle Altendorf",
    author_email='sda@fstab.net',
    license='GPLv3',
    classifiers=[
        # complete classifier list: https://pypi.org/pypi?%3Aaction=list_classifiers
        'Development Status :: 4 - Beta',
        'Environment :: Win32 (MS Windows)',
        'Environment :: X11 Applications :: Qt',
        'Intended Audience :: Developers',
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Topic :: Software Development',
        'Topic :: Utilities',
    ],
    packages=setuptools.find_packages('src'),
    package_dir={'': 'src'},
    version=pyqt5_tools_version,
    include_package_data=True,
    python_requires=">=3.5",
    install_requires=[
        'click',
        'pyqt5=={}'.format(pyqt_version),
        'pyqt{}-plugins{}{}'.format(
            pyqt_major_version,
            pyqt_plugins_version_specifier,
            pyqt_plugins_url,
        ),
        'python-dotenv',
    ],
    entry_points={
        'console_scripts': [
            'pyqt{}-tools = pyqt5_tools.entrypoints:main'.format(pyqt_major_version),
        ]
    }
)
