import datetime
import zipfile

import dateutil.parser
import moto
import pytest

from preservicaservice import errors
from preservicaservice import tasks
from preservicaservice.errors import MalformedBodyError
from preservicaservice.s3_url import S3Url
from .helpers import (
    assert_file_contents, assert_zip_contains,
    create_bucket
)


@pytest.fixture
def file_task1():
    yield tasks.FileTask(
        S3Url('s3://bucket/the/prefix/foo'),
        tasks.FileMetadata(fileName='baz.pdf'),
        'message_id',
    )


@pytest.fixture
def file_task2():
    yield tasks.FileTask(
        S3Url('s3://bucket/the/prefix/bar'),
        tasks.FileMetadata(fileName='bam.pdf'),
        'message_id',
    )


@pytest.fixture
def task(file_task1, file_task2):
    yield tasks.BaseMetadataCreateTask(
        {'foo': 'bar'},
        [file_task1, file_task2],
        S3Url('s3://upload/to'),
        'message_id',
        'role',
    )


def test_bundle_meta(temp_file, task):
    task.bundle_meta(temp_file)
    assert_zip_contains(
        temp_file,
        'message_id.metadata',
        partial='<root><foo type="str">bar</foo>',
    )


def test_collect_meta(temp_file, temp_file2, temp_file3, task):
    with open(temp_file2, 'w') as f:
        f.write('x' * 10000)

    with open(temp_file3, 'w') as f:
        f.write('x' * 90000)

    with zipfile.ZipFile(temp_file, 'w', compression=zipfile.ZIP_DEFLATED) as f:
        f.write(temp_file2, 'foo')
        f.write(temp_file3, 'bar')

    metadata = task.collect_meta(temp_file)

    assert len(metadata.keys()) == 9
    assert metadata['key'] == 'message_id'
    assert metadata['bucket'] == 'upload'
    assert metadata['status'] == 'ready'
    assert metadata['name'] == 'message_id.zip'
    assert metadata['size'] == '317'
    assert metadata['size_uncompressed'] == '100000'
    assert (
        datetime.datetime.now() -
        dateutil.parser.parse(metadata['createddate'])
    ).total_seconds() < 10
    assert metadata['createdby'] == 'role'
    assert metadata['collectionname'] == 'Preservica'


@moto.mock_s3
def test_upload_override(task, temp_file, temp_file2):
    bucket = create_bucket()

    with open(temp_file, 'w') as f:
        f.write('bundle')

    task.upload_bundle(
        S3Url('s3://bucket/path'),
        temp_file, {'foo': 'bar'},
        True,
    )

    bucket.download_file('path/message_id.zip', temp_file2)
    assert_file_contents(temp_file2, 'bundle')


@moto.mock_s3
def test_upload_no_override(task, temp_file):
    bucket = create_bucket('bucket')
    bucket.put_object(Key='prefix/foo/message_id.zip', Body='value')

    with open(temp_file, 'w') as f:
        f.write('bundle')

    with pytest.raises(errors.ResourceAlreadyExistsError):
        task.upload_bundle(
            S3Url('s3://bucket/prefix/foo'), temp_file, {}, False,
        )


@pytest.mark.parametrize(
    'message, expected', [
        (
            {
                'messageBody': {
                    'objectOrganisationRole': [{
                        'organisation': {
                            'organisationJiscId': 1,
                        },
                    }],
                },
            }, '1',
        ),
        (
            {
                'messageBody': {
                    'objectOrganisationRole': [
                        {
                            'organisation': {
                                'organisationJiscId': 1,
                            },
                        }, {
                            'organisation': {
                                'organisationJiscId': 2,
                            },
                        },
                    ],
                },
            }, '1',
        ),
    ],
)
def test_require_organisation_id_succeeds(message, expected):
    assert tasks.require_organisation_id(message) == expected


@pytest.mark.parametrize(
    'message, error', [
        ({}, 'objectOrganisationRole'),
        ({'messageBody': {}}, 'objectOrganisationRole'),
        ({'messageBody': {'objectOrganisationRole': {}}}, 'objectOrganisationRole'),
        ({'messageBody': {'objectOrganisationRole': []}}, 'objectOrganisationRole'),
        (
            {'messageBody': {'objectOrganisationRole': [
                {'organisation': ''},
            ]}}, 'organisationJiscId',
        ),
        (
            {'messageBody': {'objectOrganisationRole': [
                {'organisation': {'organisationJiscId': None}},
            ]}}, 'organisationJiscId',
        ),
    ],
)
def test_require_organisation_raises(message, error):
    with pytest.raises(MalformedBodyError, match=error):
        tasks.require_organisation_id(message)


@pytest.mark.parametrize(
    'message, expected', [
        (
            {
                'messageBody': {
                    'objectOrganisationRole': [
                        {'role': 1},
                    ],
                },
            }, '1',
        ),
        (
            {
                'messageBody': {
                    'objectOrganisationRole': [
                        {'role': 1},
                        {'role': 2},
                    ],
                },
            }, '1',
        ),
    ],
)
def test_require_organisation_role_succeeds(message, expected):
    assert tasks.require_organisation_role(message) == expected


@pytest.mark.parametrize(
    'message, error', [
        ({}, 'objectOrganisationRole'),
        ({'messageBody': {}}, 'objectOrganisationRole'),
        ({'messageBody': {'objectOrganisationRole': {}}}, 'objectOrganisationRole'),
        ({'messageBody': {'objectOrganisationRole': []}}, 'objectOrganisationRole'),
        (
            {'messageBody': {
                'objectOrganisationRole': [
                    {'role': ''},
                ],
            }},
            'objectOrganisationRole.role',
        ),
        (
            {'messageBody': {
                'objectOrganisationRole': [
                    {'role': None},
                ],
            }},
            'objectOrganisationRole.role',
        ),
    ],
)
def test_require_organisation_role_raises(message, error):
    with pytest.raises(MalformedBodyError, match=error):
        tasks.require_organisation_role(message)


@pytest.mark.parametrize(
    'argument, expected', [
        ('s3://bucket/foo/bar/baz', 'message_id/foo/bar'),
        ('s3://bucket/foo/bar', 'message_id/foo'),
        ('s3://bucket/foo/', 'message_id/foo'),
        ('s3://bucket/foo', 'message_id'),
    ],
)
def test_get_base_archive_path(argument, expected):
    assert tasks.get_base_archive_path(
        S3Url.parse(argument),
        'message_id',
    ) == expected
