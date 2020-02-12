import os
import pathlib
import sys

here = pathlib.Path(__file__).parent

sys.path.insert(0, here)
# TODO: yuck, put the build command in a separate project and
#       build-requires it?
import build_new
sys.path.pop(0)

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
    pad_version(os.environ['PYQT_VERSION']),
    version.version,
))

# sys.stderr.write('another stderr test from {}\n'.format(__file__))

with open('README.rst') as f:
    readme = f.read()

console_scripts = [
    'pyqt5toolsinstalluic = pyqt5_tools.entrypoints:pyqt5toolsinstalluic',
    'pyqt5designer = pyqt5_tools.entrypoints:pyqt5designer',
    'pyqt5qmlscene = pyqt5_tools.entrypoints:pyqt5qmlscene',
    'pyqt5qmltestrunner = pyqt5_tools.entrypoints:pyqt5qmltestrunner',
]

# print('--- console_scripts')
# for console_script in console_scripts:
#     print('    ' + repr(console_script))

# # TODO: do i really need this?  seems like it could be specified to be
# #       specific to whatever is running it without saying what that is
# #       or that it would default to that
# build_new.write_setup_cfg(here)

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
        'Programming Language :: Python :: 3.8',
        'Topic :: Software Development',
        'Topic :: Utilities',
    ],
    cmdclass={'build_py': build_new.BuildPy},
    packages=setuptools.find_packages('src'),
    package_dir={'': 'src'},
    version=version,
    include_package_data=True,
    python_requires=">=3.5",
    install_requires=[
        'click',
        'python-dotenv',
        'pyqt5=={}'.format(os.environ['PYQT_VERSION']),
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
