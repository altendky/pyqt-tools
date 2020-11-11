import faulthandler
faulthandler.enable()

import inspect
import itertools
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
import traceback
import typing

import attr
import hyperlink
import lddwrap
import patch
import requests
import setuptools.command.build_py
import tenacity


fspath = getattr(os, 'fspath', str)


class BuildPy(setuptools.command.build_py.build_py):
    def build_packages(self):
        super().build_packages()

        try:
            [package_name] = (
                package
                for package in self.distribution.packages
                if '.' not in package
            )

            build_command = self.distribution.command_obj['build']

            cwd = pathlib.Path.cwd()
            lib_path = cwd / build_command.build_lib
            package_path = lib_path / package_name

            main(
                package_path=package_path,
                build_base_path=cwd / build_command.build_base,
            )

            if getattr(self.distribution, 'entry_points', None) is None:
                self.distribution.entry_points = {}
            console_scripts = self.distribution.entry_points.setdefault('console_scripts', [])
        except:
            # something apparently consumes tracebacks (not exception messages)
            # for OSError at least.  let's avoid that silliness.
            traceback.print_exc()
            raise


Collector = typing.Callable[
    [pathlib.Path, pathlib.Path],
    typing.Iterable[pathlib.Path],
]


@attr.s(frozen=True)
class Destinations:
    package = attr.ib()
    examples = attr.ib()
    qt = attr.ib()
    qt_bin = attr.ib()
    qt_plugins = attr.ib()
    qt_platforms = attr.ib()

    @classmethod
    def build(cls, package_path):
        qt = package_path / 'Qt'
        qt_bin = qt / 'bin'
        qt_plugins = qt_bin / 'plugins'
        qt_platforms = qt_plugins / 'platforms'

        return cls(
            package=package_path,
            examples=package_path / 'examples',
            qt=qt,
            qt_bin=qt_bin,
            qt_plugins=qt_plugins,
            qt_platforms=qt_platforms,
        )

    def create_directories(self):
        for path in [
            self.qt,
            self.qt_bin,
            self.qt_plugins,
            self.qt_platforms,
        ]:
            path.mkdir(parents=True, exist_ok=True)


bits = int(platform.architecture()[0][0:2])


T = typing.TypeVar('T')


@attr.s(frozen=True)
class FileCopyAction:
    source = attr.ib()
    destination = attr.ib() # including file name, relative

    @classmethod
    def from_path(
            cls: typing.Type[T],
            source: pathlib.Path,
            root: pathlib.Path,
    ) -> T:
        action = cls(
            source=source,
            destination=source.resolve().relative_to(root.resolve()),
        )

        return action

    @classmethod
    def from_tree_path(
            cls: typing.Type[T],
            source: pathlib.Path,
            root: pathlib.Path,
            filter: typing.Callable[[pathlib.Path], bool] = lambda path: True,
    ) -> typing.Set[T]:
        actions = {
            cls(
                source=source,
                destination=source.relative_to(root),
            )
            for source in source.rglob('*')
            if filter(source)
            if source.is_file()
        }

        return actions

    @tenacity.retry(
        reraise=True,
        retry=tenacity.retry_if_exception_type(
            (NotADirectoryError, FileExistsError),
        ),
        stop=tenacity.stop_after_attempt(5),
        wait=tenacity.wait_fixed(5),
    )
    def copy(self, destination_root: pathlib.Path) -> None:
        destination = destination_root / self.destination
        try:
            destination.parent.mkdir(parents=True, exist_ok=True)
        except (NotADirectoryError, FileExistsError):
            subprocess.run(['df', '-h'], check=True)
            print('destination_root', destination_root)
            print('self.source', self.source)
            print('self.destination', self.destination)
            print('destination', destination)
            print('destination.parent', destination.parent, destination.parent.is_dir(), destination.parent.is_file())
            print('destination.parent.iterdir()', list(destination.parent.iterdir()))
            raise

        shutil.copy(src=fspath(self.source), dst=fspath(destination))


def create_script_function_name(path: pathlib.Path):
    return path.stem.replace('-', '_')


def linuxdeployqt_substitute_list_source(
        target,
) -> typing.List[pathlib.Path]:
    paths = [
        dependency.path
        for dependency in lddwrap.list_dependencies(
            path=target,
        )
        if dependency.path is not None
    ]

    return paths


def linux_executable_copy_actions(
        source_path: pathlib.Path,
        reference_path: pathlib.Path,
) -> typing.Set[FileCopyAction]:
    actions = {
        FileCopyAction.from_path(
            source=source_path,
            root=reference_path,
        ),
        *(
            FileCopyAction.from_path(
                source=path,
                root=reference_path,
            )
            for path in filtered_relative_to(
                base=reference_path,
                paths=linuxdeployqt_substitute_list_source(
                    target=source_path,
                ),
            )
        ),
    }

    return actions


def win32_executable_copy_actions(
        source_path: pathlib.Path,
        reference_path: pathlib.Path,
        windeployqt: pathlib.Path,
) -> typing.Set[FileCopyAction]:
    actions = {
        FileCopyAction.from_path(
            source=source_path,
            root=reference_path,
        ),
        *(
            FileCopyAction.from_path(
                source=path,
                root=reference_path,
            )
            for path in filtered_relative_to(
                base=reference_path,
                paths=windeployqt_list_source(
                    target=source_path,
                    windeployqt=windeployqt,
                ),
            )
        ),
    }

    return actions


def darwin_executable_copy_actions(
        source_path: pathlib.Path,
        reference_path: pathlib.Path,
        # TODO: shouldn't need this once using a real lib to identify dependencies
        lib_path: pathlib.Path,
) -> typing.Set[FileCopyAction]:
    actions = {
        FileCopyAction.from_path(
            source=source_path,
            root=reference_path,
        ),
        *FileCopyAction.from_tree_path(
            source=lib_path,
            root=reference_path,
        ),
    }

    return actions


@attr.s(frozen=True)
class QtPaths:
    compiler = attr.ib()
    bin = attr.ib()
    lib = attr.ib()
    translation = attr.ib()
    qmake = attr.ib()
    windeployqt = attr.ib()
    platform_plugins = attr.ib()

    @classmethod
    def build(
            cls,
            base,
            version,
            compiler,
            platform_,
    ):
        compiler_path = base / version / compiler
        bin_path = compiler_path / 'bin'
        lib_path = compiler_path / 'lib'
        translation_path = compiler_path / 'translations'

        windeployqt = bin_path / 'windeployqt.exe'

        # TODO: CAMPid 05470781340806731460631
        qmake_suffix = ''
        extras = {}
        if platform_ == 'win32':
            qmake_suffix = '.exe'
            extras['windeployqt'] = windeployqt
        elif platform_ == 'darwin':
            extras['lib_path'] = lib_path

        return cls(
            compiler=compiler_path,
            bin=bin_path,
            lib=lib_path,
            translation=translation_path,
            qmake=(bin_path / 'qmake').with_suffix(qmake_suffix),
            windeployqt=windeployqt,
            platform_plugins=compiler_path / 'plugins' / 'platforms',
        )


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
    if cwd is not None:
        cwd = fspath(cwd)
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
        platform = sys.platform
        qt_version = environment['QT_VERSION']

        if platform == 'linux':
            qt_compiler = 'gcc_64'
            qt_architecture = 'gcc_64'
        elif platform == 'macos':
            qt_compiler = 'clang_64'
            qt_architecture = 'clang_64'
        elif platform == 'win32':
            # TODO: change the actual storage
            
            if tuple(int(s) for s in qt_version.split('.')) >= (5, 15):
                year = '2019'
            else:
                year = '2017'

            qt_compiler = 'msvc{year}'.format(year=year)
            qt_architecture = 'win{bits}_msvc{year}'.format(
                year=year,
                bits=bits,
            )

            if bits == 64:
                qt_compiler += '_64'
                qt_architecture += '_64'

        return cls(
            qt_version=qt_version,
            qt_path=build_path / 'qt',
            qt_architecture=qt_architecture,
            qt_compiler=qt_compiler,
            pyqt_version=environment['PYQT_VERSION'],
            pyqt_source_path=build_path / 'pyqt5',
            platform=platform,
            architecture=qt_architecture,
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
        **kwargs
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


@attr.s
class LinuxPlugin:
    original_path = attr.ib()
    relative_path = attr.ib()
    copy_actions = attr.ib()

    @classmethod
    def from_name(
            cls: typing.Type[T],
            name: str,
            reference_path: pathlib.Path,
            plugin_path: pathlib.Path,
    ) -> T:
        file_name = 'libq{}.so'.format(name)
        path = plugin_path / file_name

        copy_actions = linux_executable_copy_actions(
            source_path=path,
            reference_path=reference_path,
        )

        return cls(
            original_path=path,
            relative_path=path.relative_to(reference_path),
            copy_actions=copy_actions,
        )


@attr.s
class Win32Plugin:
    original_path = attr.ib()
    relative_path = attr.ib()
    copy_actions = attr.ib()

    @classmethod
    def from_name(
            cls: typing.Type[T],
            name: str,
            reference_path: pathlib.Path,
            plugin_path: pathlib.Path,
            windeployqt: pathlib.Path,
    ) -> T:
        file_name = 'q{}.dll'.format(name)
        path = plugin_path / file_name

        copy_actions = win32_executable_copy_actions(
            source_path=path,
            reference_path=reference_path,
            windeployqt=windeployqt,
        )

        return cls(
            original_path=path,
            relative_path=path.relative_to(reference_path),
            copy_actions=copy_actions,
        )


@attr.s
class DarwinPlugin:
    original_path = attr.ib()
    relative_path = attr.ib()
    copy_actions = attr.ib()

    @classmethod
    def from_name(
            cls: typing.Type[T],
            name: str,
            reference_path: pathlib.Path,
            plugin_path: pathlib.Path,
            lib_path: pathlib.Path,
    ) -> T:
        file_name = 'libq{}.dylib'.format(name)
        path = plugin_path / file_name

        copy_actions = darwin_executable_copy_actions(
            source_path=path,
            reference_path=reference_path,
            lib_path=lib_path,
        )

        return cls(
            original_path=path,
            relative_path=path.relative_to(reference_path),
            copy_actions=copy_actions,
        )


def main(package_path, build_base_path):
    print('before ---!!!', file=sys.stderr)
    # TODO: uhhh....  i'm trying to use an existing directory i thought
    build_base_path.mkdir(parents=True, exist_ok=True)
    build_path = tempfile.mkdtemp(
        prefix='pyqt5_plugins-',
        dir=fspath(build_base_path),
    )
    print('after ---!!!', file=sys.stderr)
    build_path = pathlib.Path(build_path)

    configuration = Configuration.build(
        environment=os.environ,
        build_path=build_path,
        package_path=package_path,
    )
    configuration.create_directories()

    return build(configuration=configuration)


def checkpoint(name):
    print('    ----<==== {} ====>----'.format(name))


def build(configuration: Configuration):
    checkpoint('Install Qt')
    install_qt(configuration=configuration)

    # application_filter = {
    #     'win32': lambda path: path.suffix == '.exe',
    #     'linux': lambda path: path.suffix == '',
    #     # TODO: darwin  the .app is for directories but it still grabs files but not designer...
    #     # 'darwin': lambda path: path.suffix == '.app',
    #     'darwin': lambda path: path.suffix == '',
    # }[configuration.platform]

    checkpoint('Define Paths')
    qt_paths = QtPaths.build(
        base=configuration.qt_path,
        version=configuration.qt_version,
        compiler=configuration.qt_compiler,
        platform_=configuration.platform,
    )

    destinations = Destinations.build(package_path=configuration.package_path)

    checkpoint('Create Directories')
    destinations.create_directories()

    checkpoint('Define Plugins')
    platform_plugin_type = {
        'linux': LinuxPlugin,
        'win32': Win32Plugin,
        'darwin': DarwinPlugin,
    }[configuration.platform]

    # TODO: CAMPid 05470781340806731460631
    extras = {}
    if configuration.platform == 'win32':
        extras['windeployqt'] = qt_paths.windeployqt
    elif configuration.platform == 'darwin':
        extras['lib_path'] = qt_paths.lib

    checkpoint('Download PyQt5')
    pyqt5_sdist_path = save_sdist(
        project='PyQt5',
        version=configuration.pyqt_version,
        directory=configuration.download_path,
    )

    with tarfile.open(fspath(pyqt5_sdist_path)) as tar_file:
        for member in tar_file.getmembers():
            member.name = pathlib.Path(*pathlib.Path(member.name).parts[1:])
            member.name = fspath(member.name)
            tar_file.extract(
                member=member,
                path=fspath(configuration.pyqt_source_path),
            )

    checkpoint('Patch PyQt5')
    patch_pyqt(configuration, qt_paths)

    checkpoint('Build PyQt5')
    build_path = build_pyqt(configuration, qt_paths)

    checkpoint('Build PyQt5 Plugin Copy Actions')
    all_copy_actions = {
        destinations.qt: set(),
        destinations.package: set(),
    }

    if configuration.platform == 'win32':
        designer_plugin_path = (
            build_path / 'designer' / 'release' / 'pyqt5.dll'
        )

        package_plugins = destinations.qt / 'plugins'
        package_plugins_designer = (
            package_plugins / 'designer' / designer_plugin_path.name
        )

        all_copy_actions[destinations.qt].add(FileCopyAction(
            source=designer_plugin_path,
            destination=package_plugins_designer.relative_to(destinations.qt),
        ))

        qml_plugin = build_path / 'qmlscene' / 'release' / 'pyqt5qmlplugin.dll'

        all_copy_actions[destinations.qt].add(FileCopyAction(
            source=qml_plugin,
            destination=package_plugins / qml_plugin.name,
        ))

        all_copy_actions[destinations.package].add(FileCopyAction(
            source=qml_plugin,
            destination=destinations.examples.relative_to(
                destinations.package,
            ) / qml_plugin.name,
        ))
    elif configuration.platform == 'linux':
        designer_plugin_path = build_path / 'designer' / 'libpyqt5.so'

        package_plugins = destinations.qt / 'plugins'
        package_plugins_designer = (
            package_plugins / 'designer' / designer_plugin_path.name
        )

        all_copy_actions[destinations.qt].add(FileCopyAction(
            source=designer_plugin_path,
            destination=package_plugins_designer.relative_to(destinations.qt),
        ))

        qml_plugin = (
            build_path / 'qmlscene' / 'libpyqt5qmlplugin.so'
        )

        all_copy_actions[destinations.qt].add(FileCopyAction(
            source=qml_plugin,
            destination=package_plugins / qml_plugin.name,
        ))

        all_copy_actions[destinations.package].add(FileCopyAction(
            source=qml_plugin,
            destination=destinations.examples.relative_to(
                destinations.package,
            ) / qml_plugin.name,
        ))
    # elif configuration.platform == 'darwin':
    #     package_plugins = destinations.qt / 'plugins'
    #     package_plugins_designer = package_plugins / 'designer'
    #
    #     # designer_plugin_path = build_path / 'designer' / 'libpyqt5.so'
    #     # shutil.copy(
    #     #     designer_plugin_path,
    #     #     package_plugins_designer,
    #     # )

    checkpoint('Execute Copy Actions')
    for reference, actions in sorted(all_copy_actions.items()):
        for action in sorted(actions):
            action.copy(destination_root=reference)


def filtered_relative_to(
        base: pathlib.Path,
        paths: typing.Iterable[pathlib.Path],
) -> typing.Generator[pathlib.Path, None, None]:
    for path in paths:
        try:
            path.resolve().relative_to(base.resolve())
        except (ValueError, OSError):
            print('filtering out: {}'.format(fspath(path)))
            continue

        yield path


def linux_collect_dependencies(
        source_base: pathlib.Path,
        target: pathlib.Path,
) -> typing.Generator[pathlib.Path, None, None]:
    yield from filtered_relative_to(
        base=source_base,
        paths=(
            dependency.path.resolve()
            for dependency in lddwrap.list_dependencies(path=target)
            if dependency.path is not None
        ),
    )


def darwin_collect_dependencies(
        source_base: pathlib.Path,
        target: pathlib.Path,
        lib_path: pathlib.Path,
) -> typing.Generator[pathlib.Path, None, None]:
    yield from filtered_relative_to(
        base=source_base,
        paths=(
            dependency.resolve()
            for dependency in lib_path.glob('*.framework')
        ),
    )


class DependencyCollectionError(Exception):
    pass


def windeployqt_list_source(
        target: pathlib.Path,
        windeployqt: pathlib.Path,
) -> typing.Iterable[pathlib.Path]:
    try:
        process = report_and_check_call(
            command=[
                windeployqt,
                '--dry-run',
                '--list', 'source',
                target,
            ],
            stdout=subprocess.PIPE,
            # ugh, 3.5
            # encoding='utf-8',
        )
    except subprocess.CalledProcessError as e:
        raise DependencyCollectionError(target) from e

    paths = [
        pathlib.Path(line)
        # re: .decode...  ugh, 3.5
        for line in process.stdout.decode('utf-8').splitlines()
    ]

    return paths


def patch_pyqt(configuration, qt_paths):
    # TODO: gee golly get this figured out properly and configured etc
    patch_path = (
        pathlib.Path(__file__).resolve().parent
        / 'pluginloader.{}.patch'.format(configuration.pyqt_version)
    )

    patchset = patch.fromfile(patch_path)
    patchset.apply(strip=1)


def build_pyqt(configuration, qt_paths):
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
            # TODO: don't usually want this
            # '--debug',
            '--qmake', qt_paths.qmake,
            *itertools.chain.from_iterable(
                ['--disable', module]
                for module in module_names
                if module not in (
                        {'QtCore'}                  # sip-build raises
                        | {'QtDesigner', 'QtQml'}   # what we want...  ?
                        | {'QtGui', 'QtQuick'}      # indirect dependencies
                )
            ),
        ],
        cwd=configuration.pyqt_source_path,
    )
    if configuration.platform == 'win32':
        command = ['nmake']
        env = {**os.environ, 'CL': '/MP'}
    else:
        available_cpus = os.cpu_count()

        command = ['make', '-j{}'.format(available_cpus)]
        env = {**os.environ}

    build_path = configuration.pyqt_source_path / 'build'

    report_and_check_call(
        command=command,
        env=env,
        cwd=fspath(build_path),
    )

    return build_path


def install_qt(configuration):
    report_and_check_call(
        command=[
            sys.executable,
            '-m', 'aqt',
            'install',
            '--outputdir', configuration.qt_path.resolve(),
            configuration.qt_version,
            {
                'linux': 'linux',
                'win32': 'windows',
                'darwin': 'mac',
            }[configuration.platform],
            'desktop',
            configuration.architecture,
        ],
    )