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


@pytest.mark.parametrize(
    'message, key1, key2, environment, expected', [
        (
            {'messageBody': {'objectUuid': '8fff756a-9001-4a6b-885a-ab6365284b67'}},
            'messageBody', 'objectUuid', 'test', 'test-8fff756a-9001-4a6b-885a-ab6365284b67',
        ),
        (
            {'messageBody': {'objectUuid': '4c3679ef-405c-45d0-8242-59c922bc1933'}},
            'messageBody', 'objectUuid', 'dev', 'dev-4c3679ef-405c-45d0-8242-59c922bc1933',
        ),
        (
            {'messageBody': {'objectUuid': 'c91c105c-dab8-4378-b77e-c093a91d5304'}},
            'messageBody', 'objectUuid', 'uat', 'uat-c91c105c-dab8-4378-b77e-c093a91d5304',
        ),
        (
            {'messageBody': {'objectUuid': '1afa464b-e626-42ca-a2e3-a4327b9c2386'}},
            'messageBody', 'objectUuid', 'prod', '1afa464b-e626-42ca-a2e3-a4327b9c2386',
        ),
    ],
)
def test_env_prefix_message_key(message, key1, key2, environment, expected):
    assert tasks.env_prefix_message_key(
        message, key1, key2, environment,
    ) == expected
