import moto
import pytest

from preservicaservice import errors
from preservicaservice import tasks
from preservicaservice.s3_url import S3Url
from .helpers import (
    assert_file_contents, assert_zip_contains,
    create_bucket
)


@pytest.fixture
def task():
    yield tasks.BaseMetadataCreateTask(
        'baz.pdf',
        S3Url('s3://bucket/prefix/foo')
    )


@moto.mock_s3
def test_download(temp_file, task):
    bucket = create_bucket()
    bucket.put_object(Key='prefix/foo', Body='bar')
    task.download(temp_file)
    assert_file_contents(temp_file, 'bar')


def test_generate_meta(temp_file, task):
    task.generate_meta(temp_file)
    with open(temp_file) as f:
        assert 'fileName>baz.pdf<' in f.read()


@pytest.mark.parametrize('size', [
    1, 10
])
def test_verify_limit(temp_file, size):
    with open(temp_file, 'w') as f:
        f.write(10 * 'a')
    task = tasks.BaseMetadataCreateTask('foo', 'bar', size)
    with pytest.raises(errors.UnderlyingSystemError):
        task.verify_file_size(temp_file)


def test_zip_bundle(task, temp_file, temp_file2, temp_file3):
    with open(temp_file2, 'w') as f:
        f.write('download')

    with open(temp_file3, 'w') as f:
        f.write('meta')

    task.zip_bundle(temp_file, temp_file2, temp_file3)

    assert_zip_contains(temp_file, 'prefix/foo', 'download')
    assert_zip_contains(temp_file, 'prefix/baz.metadata.xml', 'meta')


@moto.mock_s3
def test_upload_override(task, temp_file, temp_file2):
    bucket = create_bucket()

    with open(temp_file, 'w') as f:
        f.write('bundle')

    task.upload_bundle(S3Url('s3://bucket/path'), temp_file, True)

    bucket.download_file('path/prefix.zip', temp_file2)
    assert_file_contents(temp_file2, 'bundle')


@moto.mock_s3
def test_upload_no_override(task, temp_file):
    bucket = create_bucket('bucket')
    bucket.put_object(Key='prefix/foo/prefix.zip', Body='value')

    with open(temp_file, 'w') as f:
        f.write('bundle')

    with pytest.raises(errors.ResourceAlreadyExistsError):
        task.upload_bundle(S3Url('s3://bucket/prefix/foo'), temp_file, False)
