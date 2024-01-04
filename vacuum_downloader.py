#!/usr/bin/env python
import io
import os
import re
import tarfile
from pathlib import Path
from typing import Literal, TypeAlias, IO

import urllib3

VACUUM_LIB_PATH = Path(__file__).parent / 'vacuum/lib'
VACUUM_LIB_INIT_PATH = VACUUM_LIB_PATH / '__init__.py'
vacuum_version = re.search(r'vacuum_version = \'([^\']+)\'', VACUUM_LIB_INIT_PATH.read_text()).group(1)
vacuum_bin = VACUUM_LIB_PATH / 'vacuum'

PlatformString: TypeAlias = Literal['darwin', 'linux', 'windows']
ArchString: TypeAlias = Literal['arm64', 'x86_64', 'i386']

http = urllib3.PoolManager()


def download_release_tarball(
    version: str,
    plat: PlatformString,
    arch: ArchString,
) -> io.BytesIO:
    req = http.request(
        'GET',
        f'https://github.com/daveshanley/vacuum/releases/download/v{version}/vacuum_{version}_{plat}_{arch}.tar.gz',
        preload_content=False,
    )

    out = io.BytesIO()
    for chunk in req.stream(1024):
        out.write(chunk)

    out.seek(0, 0)
    return out


def extract_vacuum_binary(tarball_bytes: io.BytesIO, *, suffix: str = '') -> IO[bytes]:
    tar = tarfile.open(None, 'r:gz', tarball_bytes)
    member = tar.getmember(f'vacuum{suffix}')
    return tar.extractfile(member)


def install_vacuum_binary(binary: IO[bytes]) -> int:
    bytes_written = vacuum_bin.write_bytes(binary.read())
    vacuum_bin.chmod(0o755)
    return bytes_written


def ensure_vacuum_binary_installed(
    plat: PlatformString = os.uname().sysname,
    arch: ArchString = os.uname().machine,
    *,
    force: bool = False,
) -> int:
    if not force and vacuum_bin.exists():
        return 0

    tar_raw = download_release_tarball(vacuum_version, plat, arch)
    suffix = '.exe' if plat == 'windows' else ''
    binary = extract_vacuum_binary(tar_raw, suffix=suffix)
    return install_vacuum_binary(binary)


def get_configured_vacuum_version() -> str:
    return vacuum_version


def main():
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('--version', default=get_configured_vacuum_version())
    parser.add_argument('--platform', default='linux')
    parser.add_argument('--arch', default='x86_64')
    parser.add_argument('--force', action='store_true', default=True)
    parser.add_argument('--no-force', action='store_false', dest='force')
    args = parser.parse_args()

    bytes_written = ensure_vacuum_binary_installed(args.platform, args.arch, force=args.force)
    print(f'Wrote {bytes_written} bytes to {vacuum_bin}')


if __name__ == '__main__':
    main()
