import inspect
import os
import pathlib
import platform
import shlex
import shutil
import subprocess
import sys
import tarfile
import tempfile
import textwrap

import attr
import hyperlink
import requests


fspath = getattr(os, 'fspath', str)


@attr.s(frozen=True)
class Results:
    console_scripts = attr.ib()


@attr.s(frozen=True)
class Destinations:
    package = attr.ib()
    examples = attr.ib()
    qt = attr.ib()
    qt_bin = attr.ib()

    def create(self):
        for path in attr.asdict(self).values():
            path.mkdir(exist_ok=True)

    @classmethod
    def build(cls, base):
        package = base / 'src' / 'pyqt5_tools'
        qt = package / 'Qt'

        return cls(
            package=package,
            examples=package / 'examples',
            qt=qt,
            qt_bin=qt / 'bin',
        )


bits = int(platform.architecture()[0][0:2])

platform_names = {
    32: 'win32',
    64: 'win_amd64'
}
try:
    platform_name = platform_names[bits]
except KeyError:
    raise Exception(
        'Bit depth {bits} not recognized {options}'.format(
            bits=bits,
            options=platform_names.keys(),
        ),
    )


@attr.s(frozen=True)
class QtPaths:
    compiler = attr.ib()
    bin = attr.ib()
    windeployqt = attr.ib()
    applications = attr.ib()

    @classmethod
    def build(
            cls,
            base,
            version,
            compiler,
            application_filter=lambda path: path.suffix == '.exe',
    ):
        compiler_path = base / version / compiler
        bin_path = compiler_path / 'bin'
        applications = tuple(
            path
            for path in bin_path.glob('*')
            if application_filter(path)
        )

        return cls(
            compiler=compiler_path,
            bin=bin_path,
            windeployqt=bin_path / 'windeployqt.exe',
            applications=applications,
        )


def filter_application_paths(
        application_paths,
        destination,
        windeployqt_path,
        skip_paths=[],
):
    skip_paths = list(skip_paths)

    for application_path in application_paths:
        print('\n\nChecking: {}'.format(application_path.name))

        try:
            output = subprocess.check_output(
                [
                    windeployqt_path,
                    application_path,
                    '--dry-run',
                    '--list', 'source',
                ],
                cwd=destination,
                encoding='utf-8',
            )
        except subprocess.CalledProcessError:
            continue

        if any(fspath(path) in output for path in skip_paths):
            print('    skipped')
            continue

        yield application_path


def identify_preferred_newlines(f):
    if isinstance(f.newlines, str):
        return f.newlines
    return '\n'


# TODO: CAMPid 974597249731467124675t40136706803641679349342342
# https://github.com/altendky/altendpy/issues/8
def callers_line_info():
    here = inspect.currentframe()
    caller = here.f_back

    if caller is None:
        return None

    there = caller.f_back
    info = inspect.getframeinfo(there)

    return 'File "{}", line {}, in {}'.format(
        info.filename,
        info.lineno,
        info.function,
    )


# TODO: CAMPid 079079043724533410718467080456813604134316946765431341384014
def report_and_check_call(command, *args, cwd=None, shell=False, **kwargs):
    command = [fspath(c) for c in command]

    print('\nCalling:')
    print('    Caller: {}'.format(callers_line_info()))
    print('    CWD: {}'.format(repr(cwd)))
    print('    As passed: {}'.format(repr(command)))
    print('    Full: {}'.format(
        ' '.join(shlex.quote(fspath(x)) for x in command),
    ))

    if shell:
        print('    {}'.format(repr(command)))
    else:
        for arg in command:
            print('    {}'.format(repr(arg)))

    sys.stdout.flush()
    return subprocess.run(command, *args, cwd=cwd, check=True, **kwargs)


@attr.s(frozen=True)
class Configuration:
    qt_version = attr.ib()
    qt_path = attr.ib()
    qt_architecture = attr.ib()
    qt_compiler = attr.ib()
    pyqt_version = attr.ib()
    pyqt_source_path = attr.ib()
    platform = attr.ib()
    architecture = attr.ib()
    build_path = attr.ib()
    download_path = attr.ib()

    @classmethod
    def build(cls, environment, build_path):
        return cls(
            qt_version=environment['QT_VERSION'],
            qt_path=build_path / 'qt',
            qt_architecture=environment['QT_ARCHITECTURE'],
            qt_compiler=environment['QT_COMPILER'],
            pyqt_version=environment['PYQT_VERSION'],
            pyqt_source_path=build_path / 'pyqt5',
            platform=environment['QT_PLATFORM'],
            architecture=environment['QT_ARCHITECTURE'],
            build_path=build_path,
            download_path=build_path / 'downloads',
        )

    def create_directories(self):
        for path in [
            self.qt_path,
            self.pyqt_source_path,
            self.build_path,
            self.download_path,
        ]:
            path.mkdir(exist_ok=True)


# https://repl.it/@altendky/requests-stream-download-to-file-2
default_chunk_size = 2 ** 24


def download_base(
        file,
        method,
        url,
        *args,
        chunk_size=default_chunk_size,
        resume=True,
        **kwargs,
):
    if resume:
        headers = kwargs.get('headers', {})
        headers.setdefault('Range', 'bytes={}-'.format(file.tell()))

    response = requests.request(
        method,
        url,
        *args,
        stream=True,
        **kwargs,
    )
    response.raise_for_status()

    for chunk in response.iter_content(chunk_size=chunk_size):
        file.write(chunk)


def get_down(file, url, *args, **kwargs):
    return download_base(
        file=file,
        method='GET',
        url=url,
        *args,
        **kwargs,
    )


def save_sdist(project, version, directory):
    project_url = hyperlink.URL(
        scheme='https',
        host='pypi.org',
        path=('pypi', project, version, 'json'),
    )
    response = requests.get(project_url)
    response.raise_for_status()

    urls = response.json()['urls']

    [record] = (
        url
        for url in urls
        if url.get('packagetype') == 'sdist'
    )

    url = hyperlink.URL.from_text(record['url'])

    directory.mkdir(exist_ok=True)
    path = directory / url.path[-1]

    with path.open('wb') as file:
        get_down(file=file, url=url)

    return path


def main():
    with tempfile.TemporaryDirectory() as build_path:
        build_path = pathlib.Path(build_path)

        configuration = Configuration.build(
            environment=os.environ,
            build_path=build_path,
        )
        configuration.create_directories()

        build(configuration=configuration)


def build(configuration: Configuration):
    report_and_check_call(
        command=[
            sys.executable,
            '-m', 'aqt',
            'install',
            '--outputdir', configuration.qt_path,
            configuration.qt_version,
            configuration.platform,
            'desktop',
            configuration.architecture,
        ],
    )

    qt_paths = QtPaths.build(
        base=configuration.qt_path,
        version=configuration.qt_version,
        compiler=configuration.qt_compiler,
    )
    os.environ['PATH'] = os.pathsep.join((
        os.environ['PATH'],
        fspath(qt_paths.bin),
    ))

    with open('setup.cfg', 'w') as cfg:
        python_tag = 'cp{major}{minor}'.format(
            major=sys.version_info[0],
            minor=sys.version_info[1],
        )

        cfg.write(textwrap.dedent('''\
            [bdist_wheel]
            python-tag = {python_tag}
            plat-name = {platform_name}
        ''').format(python_tag=python_tag, platform_name=platform_name))

    destinations = Destinations.build(base=pathlib.Path(__file__).parent)
    destinations.create()

    filtered_application_paths = list(
        filter_application_paths(
            application_paths=qt_paths.applications,
            windeployqt_path=qt_paths.windeployqt,
            destination=destinations.package,
            skip_paths=['WebEngine'],
        ),
    )

    for application_path in filtered_application_paths:
        shutil.copy(application_path, destinations.qt_bin)

        report_and_check_call(
            command=[
                qt_paths.windeployqt,
                application_path.name,
            ],
            cwd=destinations.qt_bin,
        )

    entry_point_function_names = {
        path.name.replace('-', '_'): path.name
        for path in filtered_application_paths
    }

    entry_points_py = destinations.package / 'entrypoints.py'

    with entry_points_py.open(newline='') as f:
        f.read()
        newlines = identify_preferred_newlines(f)

    with entry_points_py.open('a', newline=newlines) as f:
        for function, application in entry_point_function_names.items():
            f.write(textwrap.dedent('''\
                def {function}():
                    load_dotenv()
                    return subprocess.call([
                        str(here/'Qt'/'bin'/'{application}.exe'),
                        *sys.argv[1:],
                    ])
    
    
                '''.format(
                    function=function,
                    application=application,
                )
            ))

    console_scripts = [
        '{application} = pyqt5_tools.entrypoints:{function}'.format(
            function=function,
            application=application,
        )
        for function, application in entry_point_function_names.items()
    ]

    pyqt5_sdist_path = save_sdist(
        project='PyQt5',
        version=configuration.pyqt_version,
        directory=configuration.download_path,
    )

    with tarfile.open(pyqt5_sdist_path) as tar_file:
        for member in tar_file.getmembers():
            member.name = pathlib.Path(*pathlib.Path(member.name).parts[1:])
            tar_file.extract(
                member=member,
                path=configuration.pyqt_source_path,
            )

    report_and_check_call(
        command=[
            sys.executable,
            '-c',
            '; '.join([
                'import sys',
                'import sipbuild.tools.wheel',
                'sys.argv["0"] = "sip-wheel"',
                'sipbuild.tools.wheel.main()',
            ]),
            '--confirm-license',
            '--verbose',
        ],
        cwd=configuration.pyqt_source_path,
        env={
            **os.environ,
            'PATH': os.pathsep.join((
                fspath(qt_paths.bin),
                os.environ['PATH'],
            )),
        },
    )

    return Results(console_scripts=console_scripts)
