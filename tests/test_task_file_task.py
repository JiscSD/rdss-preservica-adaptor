import moto
import pytest

from preservicaservice import errors
from preservicaservice import tasks
from preservicaservice.remote_urls import S3RemoteUrl
from .helpers import (
    assert_file_contents, assert_zip_contains,
    create_bucket
)


@pytest.fixture
def file_metadata():
    yield tasks.FileMetadata(fileName='baz.pdf')


def test_generate_meta(temp_file, file_metadata):
    file_metadata.generate(temp_file)
    with open(temp_file) as f:
        assert 'fileName>baz.pdf<' in f.read()


@pytest.fixture
def task(file_metadata):
    yield tasks.FileTask(
        S3RemoteUrl('s3://bucket/the/prefix/foo'),
        file_metadata,
        'message_id',
        'object_id',
        [],
    )


@moto.mock_s3
def test_download(temp_file, task):
    bucket = create_bucket()
    bucket.put_object(Key='the/prefix/foo', Body='bar')
    task.download(temp_file)
    assert_file_contents(temp_file, 'bar')


@pytest.mark.parametrize(
    'size', [
        1, 10,
    ],
)
def test_verify_limit(temp_file, size):
    with open(temp_file, 'w') as f:
        f.write(10 * 'a')
    task = tasks.FileTask(
        S3RemoteUrl('s3://bucket/the/prefix/foo'),
        tasks.FileMetadata(fileName='baz.pdf'),
        'message_id',
        'object_id',
        [],
        size,
    )
    with pytest.raises(errors.UnderlyingSystemError):
        task.verify_file_size(temp_file)


def test_zip_bundle(task, temp_file, temp_file2, temp_file3):
    with open(temp_file2, 'w') as f:
        f.write('download')

    with open(temp_file3, 'w') as f:
        f.write('meta')

    task.zip_bundle(temp_file, temp_file2, temp_file3)

    assert_zip_contains(
        temp_file, 'object_id/foo', 'download',
    )
    assert_zip_contains(
        temp_file, 'object_id/foo.metadata', 'meta',
    )
