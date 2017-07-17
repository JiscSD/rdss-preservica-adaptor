import pytest

from preservicaservice import s3_url


@pytest.mark.parametrize('url, expected', [
    ('s3://bucket/path/to/file.pdf', True),
    ('s3://bucket/file.pdf', True),
    ('http://bucket/file.pdf', False),
    ('s3://', False),
])
def test_is_valid_url(url, expected):
    assert s3_url.S3Url.is_valid_url(url) == expected


@pytest.mark.parametrize('url, expected', [
    ('s3://bucket/path/to/file.pdf', 'bucket'),
    ('s3://bucket', 'bucket'),
])
def test_bucket_name(url, expected):
    assert s3_url.S3Url(url).bucket_name == expected


@pytest.mark.parametrize('url, expected', [
    ('s3://bucket/path/to/file.pdf', 'path/to/file.pdf'),
    ('s3://bucket', ''),
])
def test_object_key(url, expected):
    assert s3_url.S3Url(url).object_key == expected


def test_parse_succeeds():
    raw = 's3://bucket/path/to/file.pdf'
    url = s3_url.S3Url.parse(raw)
    assert isinstance(url, s3_url.S3Url)
    assert url.url == raw


def test_parse_fails():
    with pytest.raises(ValueError):
        s3_url.S3Url.parse('http://bucket/path/to/file.pdf')
