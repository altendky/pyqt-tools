import os
import pathlib

import setuptools.build_meta


build_wheel = setuptools.build_meta.build_wheel
build_sdist = setuptools.build_meta.build_sdist
prepare_metadata_for_build_wheel = (
    setuptools.build_meta.prepare_metadata_for_build_wheel
)
get_requires_for_build_sdist = (
    setuptools.build_meta.get_requires_for_build_sdist
)


class InvalidVersionError(Exception):
    pass


def pad_version(v, segment_count=3):
    split = v.split('.')

    if len(split) > segment_count:
        raise InvalidVersionError('{} has more than three segments'.format(v))

    return '.'.join(split + ['0'] * (segment_count - len(split)))


# TODO: CAMPid 98743987416764218762139847764318798
# TODO: really doesn't seem quite proper here and probably should come
qt_version = pad_version(os.environ.setdefault('QT_VERSION', '6.1.0'))
qt_major_version = qt_version.partition('.')[0]

# Inclusive of the lower bound and exclusive of the upper
qt_applications_wrapper_range = ['2.2', '3']

# Must be False for release.  PyPI won't let you upload with a URL dependency.
use_qt_applications_url = True

if use_qt_applications_url:
    qt_applications_url = ' @ git+https://github.com/altendky/qt-applications@main'
    qt_applications_version_specifier = ''
else:
    qt_applications_url = ''
    qt_applications_version_format = '>={qt}.{wrapper[0]}, <{qt}.{wrapper[1]}'
    qt_applications_version_specifier = qt_applications_version_format.format(
        qt=qt_version,
        wrapper=qt_applications_wrapper_range,
    )


qt_applications_requirement = 'qt{}-applications{}{}'.format(
    qt_major_version,
    qt_applications_version_specifier,
    qt_applications_url,
)

requirements = {
    'attrs': '',
    'versioneer': '== 0.29',
    'wheel': '',
}


def to_list(*dicts):
    merged = {}
    for d in dicts:
        merged.update(d)

    return [
        package + more
        for package, more in merged.items()
    ]


def get_requires_for_build_wheel(config_settings=None):
    return [*to_list(requirements), qt_applications_requirement]


def create_script_function_name(path: pathlib.Path):
    return path.stem.replace('-', '_')
