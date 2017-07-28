import moto
import pytest

from preservicaservice import errors
from preservicaservice import tasks
from preservicaservice.s3_url import S3Url
from .helpers import assert_zip_contains, create_bucket


@pytest.fixture
def task():
    yield tasks.MetadataUpdateTask(
        'baz.pdf',
        S3Url('s3://bucket/prefix/foo.pdf'),
        '1'
    )


@moto.mock_s3
def test_run_skipped(valid_config):
    task = tasks.MetadataUpdateTask(
        'baz.pdf',
        S3Url('s3://bucket/prefix/foo.pdf'),
        '99'
    )

    assert task.run(valid_config) is False


@moto.mock_s3
def test_run_succeeds(temp_file, task, valid_config):
    source_bucket = create_bucket('bucket')
    source_bucket.put_object(Key='prefix/foo.pdf', Body='bar')

    upload_bucket = create_bucket('upload')

    assert task.run(valid_config)

    upload_bucket.download_file('to/prefix.zip', temp_file)

    assert_zip_contains(temp_file, 'prefix/foo.pdf', 'bar')
    assert_zip_contains(
        temp_file,
        'prefix/baz.metadata.xml',
        partial='fileName>baz.pdf<'
    )


@moto.mock_s3
def test_run_on_missing_file(task, valid_config):
    create_bucket('bucket')
    create_bucket('upload')

    with pytest.raises(errors.ResourceNotFoundError):
        task.run(valid_config)


@moto.mock_s3
def test_run_override(task, valid_config, temp_file):
    source_bucket = create_bucket()
    source_bucket.put_object(Key='prefix/foo.pdf', Body='bar')

    upload_bucket = create_bucket('upload')
    upload_bucket.put_object(Key='to/prefix.zip', Body='contents')

    task.run(valid_config)

    upload_bucket.download_file('to/prefix.zip', temp_file)

    assert_zip_contains(temp_file, 'prefix/foo.pdf', 'bar')
    assert_zip_contains(
        temp_file,
        'prefix/baz.metadata.xml',
        partial='fileName>baz.pdf<'
    )
