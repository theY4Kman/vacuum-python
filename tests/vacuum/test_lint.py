from pathlib import Path

import orjson
import pytest
from pytest_assert_utils.util import decl
from pytest_lambda import lambda_fixture, static_fixture

from vacuum import lint, lint_async
from vacuum_downloader import ensure_vacuum_binary_installed


@pytest.fixture(scope='session', autouse=True)
def ensure_vacuum_binary():
    return ensure_vacuum_binary_installed()


async def sync_linter(spec, ruleset):
    return lint(spec, ruleset=ruleset)


linter = lambda_fixture(params=[
    pytest.param(sync_linter, id='sync'),
    pytest.param(lint_async, id='async'),
])


ruleset_recommended = lambda_fixture(
    lambda: (Path(__file__).parent / 'ruleset-recommended.yaml').read_bytes(),
    scope='session',
)

ruleset_empty = static_fixture(
    orjson.dumps({'rules': {}}),
    scope='session',
)

empty_spec = static_fixture(
    orjson.dumps({
        'openapi': '3.1.0',
        'info': {
            'title': 'Empty',
            'description': 'An empty spec',
            'version': '0.1.0',
        },
    }),
    scope='session',
)


@pytest.mark.asyncio
@pytest.mark.parametrize(('spec', 'ruleset'), [
    pytest.param('', '', id='both-empty'),
    pytest.param('', 'rules: {}', id='spec-empty'),
    pytest.param('{"openapi": "3.1.0"}', '', id='ruleset-empty'),
])
async def it_throws_input_error_if_empty_inputs(linter, spec, ruleset):
    with pytest.raises(ValueError):
        await linter(spec, ruleset=ruleset)


@pytest.mark.asyncio
async def it_lints_with_empty_ruleset(linter, empty_spec, ruleset_empty):
    expected = []
    actual = await linter(empty_spec, ruleset=ruleset_empty)
    assert expected == actual


@pytest.mark.asyncio
async def it_lints_with_recommended_ruleset(linter, empty_spec, ruleset_recommended):
    results = await linter(empty_spec, ruleset=ruleset_recommended)

    missing_prop_results = [
        decl.Model(
            message=f'Schema: missing properties: {prop!r}',
            path='',
            rule_id='oas3-schema',
        )
        for prop in ('paths', 'components', 'webhooks')
    ]
    no_servers_result = decl.Model(
        message='No servers defined for the specification',
        path='$.servers',
        rule_id='oas3-api-servers',
    )

    expected = decl.List.containing_exactly(*missing_prop_results, no_servers_result)
    actual = results
    assert expected == actual
