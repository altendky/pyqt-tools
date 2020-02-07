import os
import pathlib
import sys

sys.path.insert(0, pathlib.Path(__file__).parent)

import build_new
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

results = build_new.main()

with open('README.rst') as f:
    readme = f.read()

console_scripts = [
    'pyqt5toolsinstalluic = pyqt5_tools.entrypoints:pyqt5toolsinstalluic',
    'pyqt5designer = pyqt5_tools.entrypoints:pyqt5designer',
    'pyqt5qmlscene = pyqt5_tools.entrypoints:pyqt5qmlscene',
    'pyqt5qmltestrunner = pyqt5_tools.entrypoints:pyqt5qmltestrunner',
    *results.console_scripts,
]

print('--- console_scripts')
for console_script in console_scripts:
    print('    ' + repr(console_script))

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
        # complete classifier list: https://pypi.org/pypi?%3Aaction=list_classifiers
        'Development Status :: 4 - Beta',
        'Environment :: Win32 (MS Windows)',
        'Intended Audience :: Developers',
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        'Operating System :: Microsoft :: Windows',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Software Development',
        'Topic :: Utilities',
    ],
    packages=setuptools.find_packages('src'),
    package_dir={'': 'src'},
    version=version,
    include_package_data=True,
    install_requires=[
        'click',
        'python-dotenv',
        'pyqt5=={}'.format(os.environ['PYQT5_VERSION']),
    ],
    entry_points={
        'console_scripts': console_scripts,
    },
#    data_files=buildinfo.data_files()
#    scripts=[
#        {scripts}
#        'pyqt5-tools/designer.exe'
#    ]
)
