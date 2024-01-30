from __future__ import annotations

import random
import string
from pathlib import Path
from string import digits
from typing import Iterable

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
        'paths': {},
    }),
    scope='session',
)


def iter_random_strings(n: int | None = None) -> Iterable[str]:
    corpus = string.ascii_lowercase + digits

    while n is None or n > 0:
        yield ''.join(random.choices(corpus, k=8))
        n -= 1


@pytest.fixture(scope='session')
def large_spec():
    spec = {
        'openapi': '3.1.0',
        'info': {
            'title': 'Large',
            'description': 'A large spec',
            'version': '0.1.0',
        },
        'tags': [],
        'paths': {},
    }

    for resource in iter_random_strings(35_000):
        spec['paths'][f'/{resource}'] = {
            'get': {
                'summary': f'List {resource} resources',
                'description': f'Returns a list of {resource} resources.',
                'operationId': f'list{resource.capitalize()}s',
                'tags': [resource],
                'responses': {
                    '200': {
                        'description': f'A list of {resource} resources.',
                        'content': {
                            'application/json': {
                                'schema': {
                                    'type': 'array',
                                    'items': {
                                        'type': 'object',
                                    },
                                },
                                'example': {},
                            },
                        },
                    },
                },
            },
        }

        spec['tags'].append({
            'name': resource,
            'description': f'A {resource} resource.',
        })

    return orjson.dumps(spec)


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
@pytest.mark.parametrize('spec_fixture', [
    pytest.param('empty_spec', id='empty'),
    pytest.param('large_spec', id='large'),
])
async def it_lints_with_recommended_ruleset(linter, request, spec_fixture, ruleset_recommended):
    spec = request.getfixturevalue(spec_fixture)
    results = await linter(spec, ruleset=ruleset_recommended)

    no_servers_result = decl.Model(
        message='no servers defined for the specification',
        path='$.servers',
        rule_id='oas3-api-servers',
    )

    expected = decl.List.containing_exactly(no_servers_result)
    actual = results
    assert expected == actual
