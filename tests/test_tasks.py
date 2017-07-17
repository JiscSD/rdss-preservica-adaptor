import pytest

from preservicaservice import errors
from preservicaservice import tasks


@pytest.mark.parametrize('url, expected', [
    ('s3://bucket/path/to/file.pdf', 'to.zip'),
    ('s3://bucket/file.pdf', 'bucket.zip'),
    ('bucket/file.pdf', 'bucket.zip'),
])
def test_zip_name_from_url(url, expected):
    assert tasks.zip_name_from_url(url) == expected


@pytest.mark.parametrize('message, key', [
    ({}, 'foo'),
    ({'messageBody': ''}, 'foo'),
    ({'messageBody': []}, 'foo'),
    ({'messageBody': {'foo': []}}, 'foo'),
    ({'messageBody': {'foo': ''}}, 'foo'),
    ({'messageBody': {'foo': ' '}}, 'foo'),
])
def test_require_non_empty_key_body_error(message, key):
    with pytest.raises(errors.MalformedBodyError):
        tasks.require_non_empty_key_body(message, key)


@pytest.mark.parametrize('message, key, expected', [
    ({'messageBody': {'foo': 'bar'}}, 'foo', 'bar'),
    ({'messageBody': {'foo': ' bar '}}, 'foo', 'bar'),
])
def test_require_non_empty_key_body_succeeds(message, key, expected):
    assert tasks.require_non_empty_key_body(message, key) == expected
