import os
import sys

import build
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

version = '.'.join((
    pad_version(os.environ['PYQT5_VERSION']),
    version.version,
))

sys.stderr.write('another stderr test from {}\n'.format(__file__))

build.main()

with open('README.rst') as f:
    readme = f.read()

setuptools.setup(
    name="pyqt5-tools",
    description="Tools to supplement the official PyQt5 wheels",
    long_description=readme,
    long_description_content_type='text/x-rst',
    url='https://github.com/altendky/pyqt5-tools',
    author="Kyle Altendorf",
    author_email='sda@fstab.net',
    license='GPLv3',
    classifiers=[
        'Environment :: Win32 (MS Windows)',
        'Intended Audience :: Developers',
        ("License :: OSI Approved :: "
         "GNU General Public License v3 (GPLv3)"),
        'Natural Language :: English',
        'Operating System :: Microsoft :: Windows',
        'Topic :: Software Development',
        'Topic :: Utilities'
    ],
    keywords='pyqt5 qt designer',
    packages=['pyqt5-tools'],
    version=version,
    include_package_data=True,
#    data_files=buildinfo.data_files()
#    scripts=[
#        {scripts}
#        'pyqt5-tools/designer.exe'
#    ]
)
