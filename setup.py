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


pyqt5_tools_wrapper_version = pad_version(versioneer.get_versions()['version'])
pyqt5_tools_version = '{}.{}'.format(pyqt_version, pyqt5_tools_wrapper_version)


# When using ~=, don't pad because that affects allowed versions
pyqt_plugins_wrapper_version = '0.1.0'
pyqt_plugins_version_specifier = '~={}.{}'.format(
    pyqt_version,
    pyqt_plugins_wrapper_version,
)
# such as:  @ git+https://github.com/altendky/pyqt5-tools@just_plugins
# or empty when using a regular index
pyqt_plugins_url = ' @ git+https://github.com/altendky/pyqt5-tools@just_plugins'


with open('README.rst') as f:
    readme = f.read()


setuptools.setup(
    name="pyqtwrappers",
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
        'pyqtplugins{}{}'.format(
            pyqt_plugins_version_specifier,
            pyqt_plugins_url,
        ),
    ],
    entry_points={
        'console_scripts': [
            'pyqttoolsinstalluic = pyqtwrappers.entrypoints:pyqttoolsinstalluic',
            'pyqtdesigner = pyqtwrappers.entrypoints:pyqtdesigner',
            'pyqtqmlscene = pyqtwrappers.entrypoints:pyqtqmlscene',
            'pyqtqmltestrunner = pyqtwrappers.entrypoints:pyqtqmltestrunner',
        ]
    }
)
