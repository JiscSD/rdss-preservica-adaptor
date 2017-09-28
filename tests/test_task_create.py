import datetime

import dateutil.parser
import moto
import pytest

from preservicaservice import errors
from preservicaservice import tasks
from preservicaservice.s3_url import S3Url
from .helpers import assert_zip_contains, create_bucket


@pytest.fixture
def file_task1():
    yield tasks.FileTask(
        S3Url('s3://bucket/unsorted/10.17863/CAM.679/data.zip'),
        tasks.FileMetadata(fileName='Label of this intellectual asset: 1'),
        'ad6dee33-80ed-ae48-9cac-ed6f2250b017',
    )


@pytest.fixture
def file_task2():
    yield tasks.FileTask(
        S3Url('s3://bucket/unsorted/10.17863/CAM.679/readme.txt'),
        tasks.FileMetadata(fileName='Label of this intellectual asset: 2'),
        'ad6dee33-80ed-ae48-9cac-ed6f2250b017',
    )


@pytest.fixture
def task(file_task1, file_task2):
    yield tasks.BaseMetadataCreateTask(
        {'foo': 'bar'},
        [file_task1, file_task2],
        S3Url('s3://upload'),
        'ad6dee33-80ed-ae48-9cac-ed6f2250b017',
        'role',
        'container_name',
    )


@moto.mock_s3
def test_run_succeeds(temp_file, task):
    source_bucket = create_bucket('bucket')
    file1_contents = 'x' * 10000
    source_bucket.put_object(Key='the/prefix/foo.pdf', Body=file1_contents)
    file2_contents = 'y' * 10000
    source_bucket.put_object(Key='the/prefix/bar.pdf', Body=file2_contents)

    upload_bucket = create_bucket('upload')

    task.run()

    upload_bucket.download_file('to/message-id.zip', temp_file)

    assert_zip_contains(
        temp_file,
        'message-id.metadata',
        partial='<root><foo type="str">bar</foo>',
    )

    assert_zip_contains(
        temp_file,
        'message-id/the/prefix/foo.pdf',
        file1_contents,
    )
    assert_zip_contains(
        temp_file,
        'message-id/the/prefix/foo.pdf.metadata',
        partial='fileName>baz.pdf<',
    )

    assert_zip_contains(
        temp_file,
        'message-id/the/prefix/bar.pdf',
        file2_contents,
    )
    assert_zip_contains(
        temp_file,
        'message-id/the/prefix/bar.pdf.metadata',
        partial='fileName>bam.pdf<',
    )

    bundle = upload_bucket.Object('to/message-id.zip')
    metadata = bundle.metadata

    assert len(metadata.keys()) == 9
    assert metadata['key'] == 'message-id'
    assert metadata['bucket'] == 'upload'
    assert metadata['status'] == 'ready'
    assert metadata['name'] == 'message-id.zip'
    assert metadata['size'] == '1179'
    assert metadata['size_uncompressed'] == '20739'
    assert (
        datetime.datetime.now() -
        dateutil.parser.parse(metadata['createddate'])
    ).total_seconds() < 10
    assert metadata['createdby'] == 'role'
    assert metadata['collectionname'] == 'Preservica'


@moto.mock_s3
def test_run_on_missing_file(task):
    create_bucket('bucket')
    create_bucket('upload')

    with pytest.raises(errors.ResourceNotFoundError):
        task.run()


@moto.mock_s3
def test_run_no_override(task):
    source_bucket = create_bucket()
    source_bucket.put_object(Key='the/prefix/foo.pdf', Body='foo')
    source_bucket.put_object(Key='the/prefix/bar.pdf', Body='bar')

    upload_bucket = create_bucket('upload')
    upload_bucket.put_object(Key='to/message-id.zip', Body='contents')

    with pytest.raises(errors.ResourceAlreadyExistsError):
        task.run()
