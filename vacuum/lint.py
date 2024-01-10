from __future__ import annotations

import asyncio
import subprocess

import orjson

from vacuum.exceptions import VacuumError, VacuumInputError, VacuumFatalError
from vacuum.lib import vacuum_bin
from vacuum.results import LintResult, parse_result
from vacuum.util import StaticContentNamedPipe


def lint(spec: str | bytes, *, ruleset: str | bytes) -> list[LintResult]:
    spec, ruleset = _handle_spec_ruleset_input(spec, ruleset)

    with StaticContentNamedPipe(ruleset, mode='wb') as ruleset_pipe:
        args = _format_report_args(
            '--ruleset', ruleset_pipe,
        )
        proc = subprocess.Popen(
            args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            pass_fds=[ruleset_pipe],
        )
        stdout_bytes, stderr_bytes = proc.communicate(spec)

    return _finalize_report_proc(proc, stdout_bytes, stderr_bytes)


async def lint_async(spec: str | bytes, *, ruleset: str | bytes) -> list[LintResult]:
    spec, ruleset = _handle_spec_ruleset_input(spec, ruleset)

    with StaticContentNamedPipe(ruleset, mode='wb') as ruleset_pipe:
        args = _format_report_args(
            '--ruleset', ruleset_pipe,
        )
        proc = await asyncio.create_subprocess_exec(
            *args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            # NOTE: our fancy named pipe object is explicitly converted to int
            #       under asyncio, to support uvloop (and possibly other
            #       loops), which does not integerize objects passed here.
            pass_fds=[int(ruleset_pipe)],
        )
        stdout_bytes, stderr_bytes = await proc.communicate(spec)

    return _finalize_report_proc(proc, stdout_bytes, stderr_bytes)


def _format_report_args(*extra) -> list[str]:
    return [
        str(vacuum_bin),
        'report',
        '--no-pretty',
        '--no-style',
        '--stdin',
        '--stdout',
        *extra,
    ]


def _handle_spec_ruleset_input(spec: str | bytes, ruleset: str | bytes) -> tuple[bytes, bytes]:
    if not spec or not ruleset:
        raise VacuumInputError('spec and ruleset must be non-empty')

    if isinstance(spec, str):
        spec = spec.encode('utf-8')
    if isinstance(ruleset, str):
        ruleset = ruleset.encode('utf-8')

    return spec, ruleset


def _finalize_report_proc(
    proc: subprocess.Popen | asyncio.subprocess.Process,
    stdout_bytes: bytes,
    stderr_bytes: bytes,
) -> list[LintResult]:
    if proc.returncode == 2:
        raise VacuumFatalError(stderr_bytes.decode('utf-8'))

    if proc.returncode != 0:
        raise VacuumError(stdout_bytes.decode('utf-8'))

    return parse_vacuum_report(stdout_bytes)


def parse_vacuum_report(stdout_bytes: bytes) -> list[LintResult]:
    report = orjson.loads(stdout_bytes)
    try:
        raw_results = report['resultSet']['results']
    except KeyError:
        return []

    return [parse_result(raw_result) for raw_result in raw_results]
