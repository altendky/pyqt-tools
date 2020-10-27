import os

import setuptools
import vcversioner


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
os.environ.setdefault('PYQT_VERSION', '5.15.1')
os.environ.setdefault('QT_VERSION', '5.15.1')

version = '.'.join((
    pad_version(os.environ['PYQT_VERSION']),
    version.version,
))

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
    version=version,
    include_package_data=True,
    python_requires=">=3.5",
    install_requires=[
        'click',
        'pyqt5=={}'.format(os.environ['PYQT_VERSION']),
        'pyqtplugins @ git+https://github.com/altendky/pyqt5-tools@just_plugins',
        'qttools @ git+https://github.com/altendky/pyqt5-tools@just_applications',
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
