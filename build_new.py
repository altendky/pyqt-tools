import inspect
import itertools
import os
import pathlib
import platform
import shlex
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import textwrap
import typing

import attr
import hyperlink
import psutil
import requests
import setuptools.command.build_py


fspath = getattr(os, 'fspath', str)


class BuildPy(setuptools.command.build_py.build_py):
    def run(self):
        super().run()

        [package_name] = (
            package
            for package in self.distribution.packages
            if '.' not in package
        )

        build_command = self.distribution.command_obj['build']

        cwd = pathlib.Path.cwd()
        lib_path = cwd / build_command.build_lib
        package_path = lib_path / package_name

        results = main(
            package_path=package_path,
            build_base_path=cwd / build_command.build_base,
        )

        console_scripts = self.distribution.entry_points['console_scripts']
        console_scripts.extend(results.console_scripts)


@attr.s(frozen=True)
class Results:
    console_scripts = attr.ib()


@attr.s(frozen=True)
class Destinations:
    package = attr.ib()
    examples = attr.ib()
    qt = attr.ib()
    qt_bin = attr.ib()

    @classmethod
    def build(cls, package_path):
        qt = package_path / 'Qt'

        return cls(
            package=package_path,
            examples=package_path / 'examples',
            qt=qt,
            qt_bin=qt / 'bin',
        )

    def create_directories(self):
        for path in [
            self.qt,
            self.qt_bin,
        ]:
            path.mkdir(parents=True, exist_ok=True)


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
class Application:
    original_path = attr.ib()
    relative_path = attr.ib()
    file_name = attr.ib()
    identifier = attr.ib()

    @classmethod
    def build(cls, path):
        relative_path = path.relative_to(path.parent)

        return cls(
            original_path=path,
            relative_path=relative_path,
            file_name=path.name,
            identifier=path.stem.replace('-', '_'),
        )


@attr.s(frozen=True)
class QtPaths:
    compiler = attr.ib()
    bin = attr.ib()
    deployqt = attr.ib()
    qmake = attr.ib()
    applications = attr.ib()

    @classmethod
    def build(
            cls,
            base,
            version,
            compiler,
            platform_,
            deployqt,
            application_filter=lambda path: path.suffix != '.conf',
    ):
        compiler_path = base / version / compiler
        bin_path = compiler_path / 'bin'
        applications = tuple(
            Application.build(path=path)
            for path in bin_path.glob('*')
            if application_filter(path)
        )

        if platform_ == 'windows':
            suffix = '.exe'
        else:
            suffix = ''

        return cls(
            compiler=compiler_path,
            bin=bin_path,
            deployqt=bin_path / deployqt,
            qmake=(bin_path / 'qmake').with_suffix(suffix),
            applications=applications,
        )


def filter_application_paths(
        applications,
        destination,
        deployqt_path,
        skip_paths=[],
) -> typing.Generator[Application, None, None]:
    skip_paths = list(skip_paths)

    for application in applications:
        print('\n\nChecking: {}'.format(application.file_name))

        try:
            output = subprocess.check_output(
                [
                    fspath(deployqt_path),
                    fspath(application.original_path),
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

        yield application


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
    package_path = attr.ib()

    @classmethod
    def build(cls, environment, build_path, package_path):
        return cls(
            qt_version=environment['QT_VERSION'],
            qt_path=build_path / 'qt',
            qt_architecture=environment['QT_ARCHITECTURE'],
            qt_compiler=environment['QT_COMPILER'],
            pyqt_version=environment['PYQT_VERSION'],
            pyqt_source_path=build_path / 'pyqt5',
            platform=sys.platform,
            architecture=environment['QT_ARCHITECTURE'],
            build_path=build_path,
            download_path=build_path / 'downloads',
            package_path=package_path,
        )

    def create_directories(self):
        for path in [
            self.qt_path,
            self.pyqt_source_path,
            self.build_path,
            self.download_path,
        ]:
            path.mkdir(parents=True, exist_ok=True)


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

    directory.mkdir(parents=True, exist_ok=True)
    path = directory / url.path[-1]

    with path.open('wb') as file:
        get_down(file=file, url=url)

    return path


def save_linuxdeployqt(version, directory):
    url = hyperlink.URL(
        scheme='https',
        host='github.com',
        path=(
            'probonopd',
            'linuxdeployqt',
            'releases',
            'download',
            str(version),
            'linuxdeployqt-{version}-x86_64.AppImage'.format(version=version),
        ),
    )

    directory.mkdir(parents=True, exist_ok=True)
    path = directory / url.path[-1]

    with path.open('wb') as file:
        get_down(file=file, url=url)

    st = os.stat(path)
    path.chmod(st.st_mode | stat.S_IXUSR)

    return path


def write_setup_cfg(directory):
    setup_cfg_path = directory / 'setup.cfg'

    python_tag = 'cp{major}{minor}'.format(
        major=sys.version_info[0],
        minor=sys.version_info[1],
    )

    setup_cfg_path.write_text(textwrap.dedent('''\
        [bdist_wheel]
        python-tag = {python_tag}
        plat-name = {platform_name}
    ''').format(python_tag=python_tag, platform_name=platform_name))


def main(package_path, build_base_path):
    print('before ---!!!', file=sys.stderr)
    # TODO: uhhh....  i'm trying to use an existing directory i thought
    build_base_path.mkdir(parents=True, exist_ok=True)
    build_path = tempfile.mkdtemp(prefix='pyqt5_tools-', dir=build_base_path)
    print('after ---!!!', file=sys.stderr)
    build_path = pathlib.Path(build_path)

    configuration = Configuration.build(
        environment=os.environ,
        build_path=build_path,
        package_path=package_path,
    )
    configuration.create_directories()

    return build(configuration=configuration)


def build(configuration: Configuration):
    aqt_platforms = {
        'linux': 'linux',
        'windows': 'windows',
        'darwin': 'mac',
    }
    report_and_check_call(
        command=[
            *(  # TODO: 517 yada seemingly doesn't get the right PATH
                #           on windows
                [
                    sys.executable,
                    '-m',
                ]
                if configuration.platform == 'windows'
                else []
            ),
            'aqt',
            'install',
            '--outputdir', configuration.qt_path.resolve(),
            configuration.qt_version,
            aqt_platforms[configuration.platform],
            'desktop',
            configuration.architecture,
        ],
    )

    if configuration.platform == 'linux':
        deployqt = save_linuxdeployqt(6, configuration.download_path)
        deployqt = deployqt.resolve()
    elif configuration.platform == 'windows':
        deployqt = pathlib.Path('windeployqt.exe')
    elif configuration.platform == 'darwin':
        deployqt = pathlib.Path('macdeployqt')
    else:
        raise Exception(
            'Unsupported platform: {}'.format(configuration.platform),
        )

    qt_paths = QtPaths.build(
        base=configuration.qt_path,
        version=configuration.qt_version,
        compiler=configuration.qt_compiler,
        platform_=configuration.platform,
        deployqt=deployqt,
    )

    destinations = Destinations.build(package_path=configuration.package_path)
    destinations.create_directories()

    filtered_applications = list(
        filter_application_paths(
            applications=qt_paths.applications,
            deployqt_path=qt_paths.deployqt,
            destination=destinations.package,
            skip_paths=['WebEngine'],
        ),
    )

    for application in filtered_applications:
        shutil.copy(application.original_path, destinations.qt_bin)

        report_and_check_call(
            command=[
                qt_paths.deployqt,
                application.file_name,
            ],
            cwd=destinations.qt_bin,
        )

    entry_points_py = destinations.package / 'entrypoints.py'

    with entry_points_py.open(newline='') as f:
        f.read()
        newlines = identify_preferred_newlines(f)

    with entry_points_py.open('a', newline=newlines) as f:
        f.write(textwrap.dedent('''\
        
            # ----  start of generated wrapper entry points
        
        '''))

        for application in filtered_applications:
            function_def = textwrap.dedent('''\
                def {function}():
                    load_dotenv()
                    return subprocess.call([
                        str(here/'Qt'/'bin'/'{application}'),
                        *sys.argv[1:],
                    ])
    
    
            ''')
            function_def_formatted = function_def.format(
                function=application.identifier,
                application=fspath(application.relative_path),
            )
            f.write(function_def_formatted)

        f.write(textwrap.dedent('''\

            # ----  end of generated wrapper entry points

        '''))

        console_scripts = [
            '{application} = pyqt5_tools.entrypoints:{function}'.format(
                function=application.identifier,
                application=application.file_name,
            )
            for application in filtered_applications
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

    sip_module_path = (configuration.pyqt_source_path / 'sip')

    module_names = [
        path.name
        for path in sip_module_path.iterdir()
        if path.is_dir()
    ]

    report_and_check_call(
        command=[
            'sip-build',
            '--confirm-license',
            '--verbose',
            '--no-make',
            '--no-tools',
            '--no-dbus-python',
            '--qmake', qt_paths.qmake,
            *itertools.chain.from_iterable(
                ['--disable', module]
                for module in module_names
                if module not in (
                    {'QtCore'}      # sip-build raises
                    | {'QtGui'}     # indirect dependencies
                )
            ),
        ],
        cwd=configuration.pyqt_source_path,
    )

    if configuration.platform == 'windows':
        command = ['nmake']
        env = {**os.environ, 'CL': '/MP'}
    else:
        if configuration.platform == 'darwin':
            available_cpus = psutil.cpu_count(logical=True)
        else:
            available_cpus = len(psutil.Process().cpu_affinity())

        command = ['make', '-j{}'.format(available_cpus)]
        env = {**os.environ}

    report_and_check_call(
        command=command,
        env=env,
        cwd=fspath(configuration.pyqt_source_path / 'build'),
    )

    return Results(console_scripts=console_scripts)
