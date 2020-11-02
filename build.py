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
import tempfile
import textwrap
import traceback
import typing

import attr
import hyperlink
import lddwrap
import requests
import setuptools.command.build_py


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

            results = main(
                package_path=package_path,
                build_base_path=cwd / build_command.build_base,
            )

            if getattr(self.distribution, 'entry_points', None) is None:
                self.distribution.entry_points = {}
            console_scripts = self.distribution.entry_points.setdefault('console_scripts', [])
            console_scripts.extend(results.console_scripts)
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
class Results:
    console_scripts = attr.ib()


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

# platform_names = {
#     32: 'win32',
#     64: 'win_amd64'
# }
# try:
#     platform_name = platform_names[bits]
# except KeyError:
#     raise Exception(
#         'Bit depth {bits} not recognized {options}'.format(
#             bits=bits,
#             options=platform_names.keys(),
#         ),
#     )


# @attr.s(frozen=True)
# class Application:
#     original_path = attr.ib()
#     relative_path = attr.ib()
#     file_name = attr.ib()
#     identifier = attr.ib()
#
#     @classmethod
#     def build(cls, path, relative_path):
#         return cls(
#             original_path=path,
#             relative_path=relative_path,
#             file_name=path.name,
#             identifier=path.stem.replace('-', '_'),
#         )


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

    def linux_less_specific_so_target(self: T) -> T:
        destination = self.destination

        if '.so.' in destination.name:
            marker = '.so.'
            index = destination.name.find(marker)
            index = destination.name.find('.', index + len(marker));
            less_specific = destination.with_name(destination.name[:index])

            if destination != less_specific:
                return attr.evolve(self, destination=less_specific)

        return self

    def copy(self, destination_root: pathlib.Path) -> None:
        destination = destination_root / self.destination
        destination.parent.mkdir(parents=True, exist_ok=True)

        shutil.copy(src=fspath(self.source), dst=fspath(destination))


# @attr.s(frozen=True)
# class DirectoryCopyAction:
#     source = attr.ib()
#     destination = attr.ib() # including target root directory name, relative
#
#     def copy(self, destination_root: pathlib.Path) -> None:
#         destination = destination_root / self.destination
#         destination.mkdir(parents=True, exist_ok=True)
#
#         shutil.copytree(
#             src=self.source,
#             dst=destination,
#             dirs_exist_ok=True,
#         )


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


@attr.s(frozen=True)
class LinuxExecutable:
    original_path = attr.ib()
    relative_path = attr.ib()
    executable_relative_path = attr.ib()
    path_name = attr.ib()
    script_function_name = attr.ib()
    copy_actions = attr.ib()

    @classmethod
    def from_path(
            cls: typing.Type[T],
            path: pathlib.Path,
            reference_path: pathlib.Path,
    ) -> T:
        relative_path = path.resolve().relative_to(reference_path)
        copy_actions = linux_executable_copy_actions(
            source_path=path,
            reference_path=reference_path,
        )

        return cls(
            original_path=path,
            relative_path=relative_path,
            executable_relative_path=relative_path,
            path_name=path.name,
            script_function_name=create_script_function_name(path=path),
            copy_actions=copy_actions,
        )

    @classmethod
    def list_from_directory(
            cls: typing.Type[T],
            directory: pathlib.Path,
            reference_path: pathlib.Path,
    ) -> typing.List[T]:
        applications = []

        for path in directory.iterdir():
            if not path.is_file() or path.suffix != '':
                print('skipping: {}'.format(path))
                continue

            try:
                application = cls.from_path(
                    path=path,
                    reference_path=reference_path,
                )
            except DependencyCollectionError:
                print('failed: {}'.format(path))
                continue

            print('including: {}'.format(path))
            applications.append(application)

        return applications


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


@attr.s(frozen=True)
class Win32Executable:
    original_path = attr.ib()
    relative_path = attr.ib()
    executable_relative_path = attr.ib()
    path_name = attr.ib()
    script_function_name = attr.ib()
    copy_actions = attr.ib()

    @classmethod
    def from_path(
            cls: typing.Type[T],
            path: pathlib.Path,
            reference_path: pathlib.Path,
            windeployqt: pathlib.Path,
    ) -> T:
        relative_path = path.resolve().relative_to(reference_path.resolve())
        copy_actions = win32_executable_copy_actions(
            source_path=path,
            reference_path=reference_path,
            windeployqt=windeployqt,
        )

        return cls(
            original_path=path,
            relative_path=relative_path,
            executable_relative_path=relative_path,
            path_name=path.name,
            script_function_name=create_script_function_name(path=path),
            copy_actions=copy_actions,
        )

    @classmethod
    def list_from_directory(
            cls: typing.Type[T],
            directory: pathlib.Path,
            reference_path: pathlib.Path,
            windeployqt: pathlib.Path,
    ) -> typing.List[T]:
        applications = []

        for path in directory.iterdir():
            if not path.is_file() or path.suffix != '.exe':
                print('skipping: {}'.format(path))
                continue

            try:
                application = cls.from_path(
                    path=path,
                    reference_path=reference_path,
                    windeployqt=windeployqt
                )
            except DependencyCollectionError:
                print('failed: {}'.format(path))
                continue

            print('including: {}'.format(path))
            applications.append(application)

        return applications


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
class DarwinExecutable:
    # The single-file ones

    original_path = attr.ib()
    relative_path = attr.ib()
    executable_relative_path = attr.ib()
    path_name = attr.ib()
    script_function_name = attr.ib()
    copy_actions = attr.ib()

    @classmethod
    def from_path(
            cls: typing.Type[T],
            path: pathlib.Path,
            reference_path: pathlib.Path,
            lib_path: pathlib.Path,
    ) -> T:
        relative_path = path.resolve().relative_to(reference_path)
        copy_actions = darwin_executable_copy_actions(
            source_path=path,
            reference_path=reference_path,
            lib_path=lib_path,
        )

        return cls(
            original_path=path,
            relative_path=relative_path,
            executable_relative_path=relative_path,
            path_name=path.name,
            script_function_name=create_script_function_name(path=path),
            copy_actions=copy_actions,
        )

    @classmethod
    def list_from_directory(
            cls: typing.Type[T],
            directory: pathlib.Path,
            reference_path: pathlib.Path,
            lib_path: pathlib.Path,
    ) -> typing.List[T]:
        applications = []

        for path in directory.iterdir():
            if not path.is_file() or path.suffix != '':
                print('skipping: {}'.format(path))
                continue

            try:
                application = cls.from_path(
                    path=path,
                    reference_path=reference_path,
                    lib_path=lib_path,
                )
            except DependencyCollectionError:
                print('failed: {}'.format(path))
                continue

            print('including: {}'.format(path))
            applications.append(application)

        return applications


def darwin_dot_app_copy_actions(
        source_path: pathlib.Path,
        reference_path: pathlib.Path,
        # TODO: doesn't seem like we should generally need this?  but maybe?
        lib_path: pathlib.Path,
) -> typing.Set[FileCopyAction]:
    actions = {
        FileCopyAction.from_tree_path(
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
class DarwinDotApp:
    # The *.app directory-file ones

    original_path = attr.ib()
    relative_path = attr.ib()
    executable_relative_path = attr.ib()
    path_name = attr.ib()
    script_function_name = attr.ib()
    copy_actions = attr.ib(factory=list)

    @classmethod
    def from_path(
            cls: typing.Type[T],
            path: pathlib.Path,
            reference_path: pathlib.Path,
            lib_path: pathlib.Path,
    ) -> T:
        relative_path = path.resolve().relative_to(reference_path)
        copy_actions = darwin_dot_app_copy_actions(
            source_path=path,
            reference_path=reference_path,
            lib_path=lib_path,
        )

        return cls(
            original_path=path,
            relative_path=relative_path,
            executable_relative_path=relative_path,
            path_name=path.name,
            script_function_name=create_script_function_name(path=path),
            copy_actions=copy_actions,
        )

    @classmethod
    def list_from_directory(
            cls: typing.Type[T],
            directory: pathlib.Path,
            reference_path: pathlib.Path,
            lib_path: pathlib.Path,
    ) -> typing.List[T]:
        applications = []

        for path in directory.iterdir():
            if not path.is_file() or path.suffix != '.app':
                continue

            try:
                application = cls.from_path(
                    path=path,
                    reference_path=reference_path,
                    lib_path=lib_path,
                )
            except DependencyCollectionError:
                continue

            applications.append(application)

        return applications


AnyApplication = typing.Union[
    DarwinExecutable,
    DarwinDotApp,
    Win32Executable,
]

application_types_by_platform = {   # typing.Dict[str, typing.List[AnyApplication]]
    'linux': [LinuxExecutable],
    'win32': [Win32Executable],
    'darwin': [DarwinExecutable, DarwinDotApp],
}


@attr.s(frozen=True)
class QtPaths:
    compiler = attr.ib()
    bin = attr.ib()
    lib = attr.ib()
    translation = attr.ib()
    qmake = attr.ib()
    windeployqt = attr.ib()
    applications = attr.ib()
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

        application_types = application_types_by_platform[platform_]
        applications = list(itertools.chain.from_iterable(
            application_type.list_from_directory(
                directory=bin_path,
                reference_path=compiler_path,
                **extras,
            )
            for application_type in application_types
        ))

        return cls(
            compiler=compiler_path,
            bin=bin_path,
            lib=lib_path,
            translation=translation_path,
            qmake=(bin_path / 'qmake').with_suffix(qmake_suffix),
            windeployqt=windeployqt,
            applications=applications,
            platform_plugins=compiler_path / 'plugins' / 'platforms',
        )


def filtered_applications(
        applications: typing.Iterable[AnyApplication],
        filter: typing.Callable[[pathlib.Path], bool] = lambda path: True,
) -> typing.List[AnyApplication]:
    results = []

    for application in applications:
        print('\n\nChecking: {}'.format(application.path_name))

        if any(
                filter(copy_action.destination)
                for copy_action in application.copy_actions
        ):
            print('    skipped')
            continue

        results.append(application)

    return results


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
            platform=platform,
            architecture=qt_architecture,
            build_path=build_path,
            download_path=build_path / 'downloads',
            package_path=package_path,
        )

    def create_directories(self):
        for path in [
            self.qt_path,
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


# def save_linuxdeployqt(version, directory):
#     url = hyperlink.URL(
#         scheme='https',
#         host='github.com',
#         path=(
#             'probonopd',
#             'linuxdeployqt',
#             'releases',
#             'download',
#             str(version),
#             'linuxdeployqt-{version}-x86_64.AppImage'.format(version=version),
#         ),
#     )
#
#     directory.mkdir(parents=True, exist_ok=True)
#     path = directory / url.path[-1]
#
#     with path.open('wb') as file:
#         get_down(file=file, url=url)
#
#     st = os.stat(path)
#     path.chmod(st.st_mode | stat.S_IXUSR)
#
#     return path


# def write_setup_cfg(directory):
#     setup_cfg_path = directory / 'setup.cfg'
#
#     python_tag = 'cp{major}{minor}'.format(
#         major=sys.version_info[0],
#         minor=sys.version_info[1],
#     )
#
#     setup_cfg_path.write_text(textwrap.dedent('''\
#         [bdist_wheel]
#         python-tag = {python_tag}
#         plat-name = {platform_name}
#     ''').format(python_tag=python_tag, platform_name=platform_name))


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
        prefix='qt5_applications-',
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

    checkpoint('Select Applications')
    applications = filtered_applications(
        applications=qt_paths.applications,
        filter=lambda path: (
            'webengine' in fspath(path).casefold()
            and path.suffix != '.qm'
        ),
    )

    checkpoint('Define Plugins')
    platform_plugin_names = {
        'linux': ['xcb', 'minimal'],
        'win32': ['minimal'],
        'darwin': ['cocoa'],
    }[configuration.platform]

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

    platform_plugins = [
        platform_plugin_type.from_name(
            name=name,
            plugin_path=qt_paths.platform_plugins,
            reference_path=qt_paths.compiler,
            **extras,
        )
        for name in platform_plugin_names
    ]

    checkpoint('Build Application And Platform Plugin Copy Actions')
    copy_actions = {
        *itertools.chain.from_iterable(
            application.copy_actions
            for application in applications
        ),
        *itertools.chain.from_iterable(
            plugin.copy_actions
            for plugin in platform_plugins
        ),
        *(
            FileCopyAction.from_path(
                source=path,
                root=qt_paths.compiler,
            )
            for path in filtered_relative_to(
                base=qt_paths.compiler,
                paths=qt_paths.translation.glob('*.qm'),
            )
        ),
    }

    if configuration.platform == 'linux':
        copy_actions = {
            action.linux_less_specific_so_target()
            for action in copy_actions
        }

    checkpoint('Write Entry Points')
    entry_points_py = destinations.package / 'entrypoints.py'

    console_scripts = write_entry_points(
        entry_points_py=entry_points_py,
        applications=applications,
    )

    all_copy_actions = {
        destinations.qt: copy_actions,
        destinations.package: set(),
    }

    checkpoint('Execute Copy Actions')
    for reference, actions in all_copy_actions.items():
        for action in actions:
            action.copy(destination_root=reference)

    checkpoint('Return Results')
    return Results(console_scripts=console_scripts)


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


def write_entry_points(
        entry_points_py: pathlib.Path,
        applications: typing.List[AnyApplication],
) -> typing.List[str]:
    with entry_points_py.open(newline='') as f:
        f.read()
        newlines = identify_preferred_newlines(f)
    with entry_points_py.open('a', newline=newlines) as f:
        f.write(textwrap.dedent('''\
        
            # ----  start of generated wrapper entry points
        
        '''))

        for application in sorted(applications, key=lambda a: a.path_name):
            partial_def = (
                '{function_name}'
                ' = functools.partial(run, application_name={application!r})\n'
            )
            partial_def_formatted = partial_def.format(
                function_name=application.script_function_name,
                application=application.original_path.stem,
            )
            f.write(partial_def_formatted)

        f.write(textwrap.dedent('''\

            # ----  end of generated wrapper entry points

        '''))

        console_scripts = [
            '{application} = qt5_applications.entrypoints:{function_name}'.format(
                function_name=application.script_function_name,
                application=application.original_path.stem,
            )
            for application in applications
        ]
    return console_scripts
