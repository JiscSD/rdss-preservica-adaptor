import pytest

from preservicaservice import errors
from preservicaservice import tasks


@pytest.mark.parametrize(
    'message, key1, key2', [
        ({}, 'messageBody', 'foo'),
        ({'messageBody': ''}, 'messageBody', 'foo'),
        ({'messageBody': []}, 'messageBody', 'foo'),
        ({'messageBody': {'foo': []}}, 'messageBody', 'foo'),
        ({'messageBody': {'foo': ''}}, 'messageBody', 'foo'),
    ],
)
def test_require_non_empty_key_error(message, key1, key2):
    with pytest.raises(errors.MalformedBodyError):
        tasks.require_non_empty_key(message, key1, key2)


@pytest.mark.parametrize(
    'message, key1, key2, expected', [
        ({'messageBody': {'foo': 'bar'}}, 'messageBody', 'foo', 'bar'),
        ({'messageBody': {'foo': ' '}}, 'messageBody', 'foo', ' '),
        ({'messageBody': {'foo': [1, 2]}}, 'messageBody', 'foo', [1, 2]),
    ],
)
def test_require_non_empty_key_succeeds(message, key1, key2, expected):
    assert tasks.require_non_empty_key(message, key1, key2) == expected
