import io
import os
import posixpath
import subprocess
import sys
import urllib
import zipfile

import attr
import requests


def report_and_check_call(**kwargs):
    print('\nCalling: ')

    for kwarg in ('command', 'cwd'):
        if kwarg in kwargs:
            print('    {}: {}'.format(kwarg, kwargs[kwarg]))

    # may only be required on AppVeyor
    sys.stdout.flush()

    command = kwargs.pop('command')

    subprocess.check_call(command, **kwargs)


def save_url_to_file(
        url, file_path=None, file_name=None, block_size=1024, **kwargs):
    #https://stackoverflow.com/questions/14114729/save-a-large-file-using-the-python-requests-library/14114741#14114741

    response = requests.get(url, **kwargs, stream=True)

    # Throw an error for bad status codes
    response.raise_for_status()

    if file_path is None:
        file_path = '.'

    if file_name is None:
        file_name = posixpath.basename(urllib.parse.urlparse(url).path)

    path = os.path.join(file_path, file_name)
    with open(path, 'wb') as handle:
        for block in response.iter_content(block_size):
            handle.write(block)

    return path


@attr.s(frozen=True)
class Version:
    raw_string = attr.ib(cmp=False)
    raw_sequence = attr.ib(hash=True)

    @classmethod
    def from_string(cls, s):
        return cls(raw_string=s)

    @classmethod
    def from_sequence(cls, *s):
        # TODO: use this comment instead once you can make it work
        # return cls(raw_sequence=s)
        return cls(raw_string='.'.join(str(n) for n in s))

    @raw_string.default
    def _(self):
        return '.'.join(str(x) for x in self.raw_sequence)

    @raw_sequence.default
    def _(self):
        return tuple(int(s) for s in self.raw_string.split('.'))

    def stripped(self):
        nonzero = False
        stripped = []

        for x in reversed(self.raw_sequence):
            if x != 0:
                nonzero = True

            if nonzero:
                stripped.append(x)

        return type(self).from_sequence(*reversed(stripped))

    def padded(self, levels=3):
        sequence = self.raw_sequence + (0,) * (levels - len(self.raw_sequence))

        return type(self).from_sequence(*sequence)

    def exactly(self, levels=3):
        sequence = self.raw_sequence[:levels]

        sequence = sequence + (0,) * (levels - len(sequence))

        return type(self).from_sequence(*sequence)

    def __str__(self):
        return self.raw_string


def twiddle_version():
    a = Version.from_string('5.9.1')
    for n in range(1, 5):
        print(a.exactly(n))
    b = Version.from_sequence(5, 9)

    print(a == b)
    print(a.exactly(2) == b.exactly(2))
    print(a < b)
    print(a > b)

    d = {
        a: b
    }

    print(d[Version.from_sequence(5, 9, 1)])


pyqt_to_qt_version_map = {
    Version.from_sequence(*k): Version.from_sequence(*v)
    for k, v in {
        (5, 9, 0): (5, 9, 1),
        (5, 8, 1): (5, 8),
        (5, 8, 0): (5, 8),
        (5, 7, 1): (5, 7, 1),
    }.items()
}

pyqt_to_qt_version_map = {
    Version.from_sequence(*k): Version.from_sequence(*v)
    for k, v in pyqt_to_qt_version_map.items()
}

def pyqt_to_qt_version(pyqt_version):
    return pyqt_to_qt_version_map[pyqt_version.padded(3)]


def list_missing_directories(path):
    if os.path.exists(path):
        return

    print('Path not found, breaking it down: {}'.format(path))

    path, filename = os.path.split(path.rstrip(os.path.sep))
    paths = tuple(path[:i] for i, x in enumerate(path, 1) if x == os.path.sep)

    print('Searching through:')
    for path in paths:
        print('    {}'.format(path))
        if not os.path.isdir(path):
            print('Failed to find as directory: {}'.format(path))
            break

    last_valid = os.path.dirname(path.rstrip(os.path.sep))
    print('Deepest path found: {}'.format(last_valid))

    report_and_check_call(
        command=[
            'tree',
        ],
        cwd=last_valid,
    )


pyqt_to_sip_version_map = {
    Version.from_sequence(*k): Version.from_sequence(*v)
    for k, v in {
        (5, 5, 1): (4, 17),
        (5, 6, 0): (4, 19),
        (5, 7, 1): (4, 19),
        (5, 8, 2): (4, 19, 2),
        (5, 9, 0): (4, 19, 3),
    }.items()
}

def pyqt_to_sip_version(pyqt_version):
    return pyqt_to_sip_version_map[pyqt_version.padded(3)]


def sip_name_url(version):
    name = 'sip-{}'.format(version)

    return name, (
        'http://downloads.sourceforge.net'
        '/project/pyqt/sip/{name}/{name}.zip'
        .format(name=name)
    )


def extract_zip_url(url, destination):
    r = requests.get(url)

    z = zipfile.ZipFile(io.BytesIO(r.content))
    z.extractall(path=destination)


def qt_path(version):
    return os.path.join('/', 'opt', str(version.stripped()))

def qt_bin_path(version):
    qt_version_subdir = str(version.exactly(2)).replace('.', '')

    return os.path.join(
        qt_path,
        qt_version_subdir,
        'gcc_64',
        'bin',
    )

