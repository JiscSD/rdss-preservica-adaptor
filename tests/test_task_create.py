import datetime

import dateutil.parser
import moto
import pytest

from preservicaservice import errors
from preservicaservice import tasks
from preservicaservice.remote_urls import S3RemoteUrl
from .helpers import assert_zip_contains, create_bucket


@pytest.fixture
def file_task1():
    yield tasks.FileTask(
        S3RemoteUrl('s3://bucket/the/prefix/foo.pdf'),
        tasks.FileMetadata(fileName='baz.pdf'),
        'this-is-message-uuid',
        'object-uuid',
        [],
    )


@pytest.fixture
def file_task2():
    yield tasks.FileTask(
        S3RemoteUrl('s3://bucket/the/prefix/bar.pdf'),
        tasks.FileMetadata(fileName='bam.pdf'),
        'this-is-message-uuid',
        'object-uuid',
        [],
    )


@pytest.fixture
def task(file_task1, file_task2):
    yield tasks.BaseMetadataCreateTask(
        {'foo': 'bar'},
        [file_task1, file_task2],
        S3RemoteUrl('s3://upload'),
        'this-is-message-uuid',
        'role',
        'object-uuid',
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

    upload_bucket.download_file('this-is-message-uuid', temp_file)

    assert_zip_contains(
        temp_file,
        'object-uuid/object-uuid.metadata',
        partial='<root xmlns="http://jisc.ac.uk/#rdss/schema">'
                '<foo type="str">bar</foo>',
    )

    assert_zip_contains(
        temp_file,
        'object-uuid/foo.pdf',
        file1_contents,
    )
    assert_zip_contains(
        temp_file,
        'object-uuid/foo.pdf.metadata',
        partial='fileName>baz.pdf<',
    )

    assert_zip_contains(
        temp_file,
        'object-uuid/bar.pdf',
        file2_contents,
    )
    assert_zip_contains(
        temp_file,
        'object-uuid/bar.pdf.metadata',
        partial='fileName>bam.pdf<',
    )

    bundle = upload_bucket.Object('this-is-message-uuid')
    metadata = bundle.metadata

    assert len(metadata.keys()) == 8
    assert metadata['key'] == 'this-is-message-uuid'
    assert metadata['bucket'] == 'upload'
    assert metadata['status'] == 'ready'
    assert metadata['name'] == 'this-is-message-uuid.zip'
    assert int(metadata['size_uncompressed']) > int(metadata['size'])
    assert (
        datetime.datetime.now() -
        dateutil.parser.parse(metadata['createddate'])
    ).total_seconds() < 10
    assert metadata['createdby'] == 'role'


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
    upload_bucket.put_object(
        Key='this-is-message-uuid', Body='contents',
    )

    with pytest.raises(errors.ResourceAlreadyExistsError):
        task.run()
