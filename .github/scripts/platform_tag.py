"""Retag Linux and macOS wheels with the platform tag their binaries need.

The glibc version comes from the highest GLIBC_ symbol version the ELF files
need, and the macOS version and architecture from the minos and architectures
of the Mach-O files.  The tag is set with ``wheel tags`` so that the WHEEL
metadata matches the file name.

Needs the wheel, pyelftools and macholib packages.
"""

import pathlib
import re
import subprocess
import sys
import tempfile
import zipfile

import elftools.elf.elffile
import elftools.elf.gnuversions
import macholib.mach_o
import macholib.MachO

# The oldest tags these wheels have had, never lowered so that they don't
# start installing where they never have.  manylinux_2_17 is PEP 599's
# manylinux2014.
minimum_glibc = (2, 17)
minimum_macos = (10, 14)
# Apple Silicon Macs start at macOS 11.
minimum_macos_arm64 = (11, 0)

elf_architectures = {
    "EM_X86_64": "x86_64",
    "EM_AARCH64": "aarch64",
}
macho_architectures = {
    "x86_64": "x86_64",
    "ARM64": "arm64",
}
macho_magics = {
    b"\xfe\xed\xfa\xce",
    b"\xce\xfa\xed\xfe",
    b"\xfe\xed\xfa\xcf",
    b"\xcf\xfa\xed\xfe",
    b"\xca\xfe\xba\xbe",
    b"\xca\xfe\xba\xbf",
}


class PlatformTagError(Exception):
    pass


def single(values, description):
    if len(values) != 1:
        raise PlatformTagError(f"Expected one {description}, found {sorted(values)}")
    [value] = values
    return value


def elf_requirements(path):
    with path.open("rb") as file:
        elf = elftools.elf.elffile.ELFFile(file)
        glibc = []
        for section in elf.iter_sections():
            if not isinstance(section, elftools.elf.gnuversions.GNUVerNeedSection):
                continue
            for _, auxiliaries in section.iter_versions():
                for auxiliary in auxiliaries:
                    match = re.fullmatch(r"GLIBC_(\d+)\.(\d+)(?:\.\d+)?", auxiliary.name)
                    if match is not None:
                        glibc.append((int(match[1]), int(match[2])))
        return elf_architectures[elf["e_machine"]], max([minimum_glibc, *glibc])


def unpack_macos_version(packed):
    return packed >> 16, (packed >> 8) & 0xFF


def macho_requirements(path):
    architectures = set()
    versions = []
    for header in macholib.MachO.MachO(path).headers:
        cpu_type = macholib.mach_o.CPU_TYPE_NAMES[header.header.cputype]
        architectures.add(macho_architectures[cpu_type])
        for load_command, command, _ in header.commands:
            if load_command.cmd == macholib.mach_o.LC_BUILD_VERSION:
                versions.append(unpack_macos_version(command.minos))
            elif load_command.cmd == macholib.mach_o.LC_VERSION_MIN_MACOSX:
                versions.append(unpack_macos_version(command.version))
    return frozenset(architectures), versions


def platform_tag(root):
    elf = []
    macho = []
    for path in sorted(root.rglob("*")):
        if path.is_symlink() or not path.is_file():
            continue
        with path.open("rb") as file:
            magic = file.read(4)
        if magic == b"\x7fELF":
            elf.append(elf_requirements(path))
        elif magic in macho_magics:
            macho.append(macho_requirements(path))

    if elf and macho:
        raise PlatformTagError("Found both ELF and Mach-O files")

    if elf:
        architecture = single({architecture for architecture, _ in elf}, "architecture")
        major, minor = max(glibc for _, glibc in elf)
        return f"manylinux_{major}_{minor}_{architecture}"

    if macho:
        architectures = single({architectures for architectures, _ in macho}, "architecture set")
        if architectures == {"x86_64", "arm64"}:
            architecture = "universal2"
        else:
            architecture = single(architectures, "architecture")
        versions = [version for _, file_versions in macho for version in file_versions]
        if not versions:
            raise PlatformTagError("No Mach-O file declares a minimum macOS version")
        major, minor = max([minimum_macos, *versions])
        if architecture == "arm64":
            major, minor = max((major, minor), minimum_macos_arm64)
        if major >= 11:
            # pip only matches macOS 11 and later tags with a zero minor version.
            minor = 0
        return f"macosx_{major}_{minor}_{architecture}"

    raise PlatformTagError("Found no ELF or Mach-O files")


def main(wheel):
    wheel = pathlib.Path(wheel)
    with tempfile.TemporaryDirectory() as directory:
        with zipfile.ZipFile(wheel) as archive:
            archive.extractall(directory)
        tag = platform_tag(pathlib.Path(directory))

    print(f"{wheel.name}: {tag}")
    subprocess.run(
        [sys.executable, "-m", "wheel", "tags", "--remove", "--platform-tag", tag, wheel],
        check=True,
    )


main(*sys.argv[1:])
