import shutil
import sys
from pathlib import Path

import setuptools


def build(setup_kwargs):
    """Builds wheels for all supported platforms"""
    egg_base = Path.cwd() / 'build'
    # start fresh
    if egg_base.exists():
        shutil.rmtree(egg_base)
    egg_base.mkdir(parents=True, exist_ok=True)

    sys.path.insert(0, str(egg_base / 'lib'))
    from vacuum_downloader import ensure_vacuum_binary_installed

    for plat, arch in [
        ('darwin', 'arm64'),
        ('darwin', 'x86_64'),
        ('linux', 'arm64'),
        ('linux', 'i386'),
        ('linux', 'x86_64'),
        ('windows', 'arm64'),
        ('windows', 'i386'),
        ('windows', 'x86_64'),
    ]:
        ensure_vacuum_binary_installed(plat, arch, force=True)

        setuptools.setup(
            **setup_kwargs,
            script_args=['bdist_wheel'],
            options={
                'bdist_wheel': {
                    'plat_name': f'{plat}_{arch}',
                    'bdist_dir': f'{egg_base}/lib',
                    'keep_temp': True,
                },
                'egg_info': {'egg_base': str(egg_base)}
            }
        )
