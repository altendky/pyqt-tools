import setuptools


setuptools.setup(
    name="pyqt5toolsbuild",
    packages=setuptools.find_packages(),
    entry_points={
        'console_scripts': [
            'before_install = pyqt5toolsbuild.linux.before_install:main',
            'deploy_qt = pyqt5toolsbuild.linux.deploy_qt:main',
            'buildlinux = pyqt5toolsbuild.linux.build:main',
        ]
    },
)
