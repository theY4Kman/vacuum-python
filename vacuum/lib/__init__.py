from pathlib import Path

__all__ = ['vacuum_bin', 'vacuum_version']

vacuum_bin = Path(__file__).parent / 'vacuum'
vacuum_version = '0.6.3'
