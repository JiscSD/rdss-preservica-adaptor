import base64
import json
from collections import namedtuple
import moto

import pytest

from preservicaservice import errors
from preservicaservice import tasks
from preservicaservice import tasks_parser
from preservicaservice.config import Config
from .test_preservica_s3_bucket import mock_preservica_bucket_builder
from .helpers import create_bucket

Record = namedtuple('Record', 'data')


def to_base64(value, encoding='utf-8'):
    value = base64.b64encode(bytes(value, encoding))
    return str(value, 'utf-8')


def to_record(data):
    return Record(to_base64(json.dumps(data)))


@pytest.mark.parametrize(
    'data, error', [
        (None, errors.MalformedJsonBodyError),
        (to_base64('abc', encoding='koi8-r'), errors.MalformedJsonBodyError),
        (to_base64('[1,2]'), errors.MalformedJsonBodyError),
    ],
)
def test_decode_record_error(data, error):
    with pytest.raises(error):
        tasks_parser.decode_record(Record(str(data)))


@pytest.mark.parametrize(
    'data, value', [
        (to_base64('{"a": "b"}'), {'a': 'b'}),
    ],
)
def test_decode_record(data, value):
    assert tasks_parser.decode_record(Record(str(data))) == value


@pytest.mark.parametrize(
    'message, error', [
        ({}, errors.MalformedHeaderError),
        ({'messageHeader': {}}, errors.MalformedHeaderError),
        ({'messageHeader': {'messageType': []}}, errors.MalformedHeaderError),
        (
            {'messageHeader': {'messageType': 'abc'}},
            errors.UnsupportedMessageTypeError,
        ),
    ],
)
def test_create_supported_task_error(message, error, valid_config):
    with pytest.raises(error):
        tasks_parser.create_supported_tasks(message, valid_config)


def valid_create_publisher():
    return [
        {
            'organisation': {
                'organisationJiscId': 1,
            },
            'role': 123,
        },
    ]


def valid_create_header():
    return {
        'messageId': 'message_id',
        'messageType': tasks.MetadataCreateTask.TYPE,
    }


def valid_create_object_file():
    return [
        {
            'fileStorageLocation': 's3://bucket/path/to/file',
            'fileName': 'filename',
            'storagePlatformType': 1,
            'fileChecksum': [],
        },
    ]


@mock_preservica_bucket_builder()
def test_metadata_create_task(valid_config):
    record = to_record({
        'messageHeader': valid_create_header(),
        'messageBody': {
            'objectUuid': 'object_uuid',
            'objectFile': [
                {
                    'fileStorageLocation': 's3://bucket/path/to/file',
                    'fileName': 'filename',
                    'fileStoragePlatform': {
                        'storagePlatformType': 1,
                    },
                    'fileChecksum': [],
                },
                {
                    'fileStorageLocation': 's3://bucket/path/to/file2',
                    'fileName': 'filename2',
                    'fileStoragePlatform': {
                        'storagePlatformType': 1,
                    },
                    'fileChecksum': [],
                },
            ],
            'objectOrganisationRole': [{
                'organisation': {
                    'organisationJiscId': 1,
                    'organisationName': 'string',
                    'organisationType': 2,
                    'organisationAddress': 'string',
                },
                'role': 3,
            }],
        },
    })
    task = tasks_parser.record_to_task(record, valid_config)

    assert isinstance(task, tasks.MetadataCreateTask)
    assert task.destination_bucket.name == 'com.preservica.rdss.jisc.preservicaadaptor'
    assert task.message_id == 'test-message_id'
    assert task.role == '3'

    assert len(task.file_tasks) == 2

    file_task = task.file_tasks[0]
    assert file_task.remote_file.url == 's3://bucket/path/to/file'
    assert file_task.metadata.fileName == 'filename'

    file_task = task.file_tasks[1]
    assert file_task.remote_file.url == 's3://bucket/path/to/file2'
    assert file_task.metadata.fileName == 'filename2'


@mock_preservica_bucket_builder()
def test_metadata_create_task_skipped(valid_config):
    record = to_record({
        'messageHeader': valid_create_header(),
        'messageBody': {
            'objectFile': [
                {
                    'fileStorageLocation': 's3://bucket/path/to/file',
                    'fileName': 'filename',
                    'fileStoragePlatform': {
                        'storagePlatformType': 1,
                    },
                    'fileChecksum': [],
                },
                {
                    'fileStorageLocation': 's3://bucket/path/to/file2',
                    'fileName': 'filename2',
                    'fileStoragePlatform': {
                        'storagePlatformType': 1,
                    },
                    'fileChecksum': [],
                },
            ],
            'objectOrganisationRole': [{
                'organisation': {
                    'organisationJiscId': 999,
                },
                'role': 3,
            }],
        },
    })
    with pytest.raises(errors.MalformedBodyError):
        tasks_parser.record_to_task(record, valid_config)


@pytest.mark.parametrize(
    'message, error', [
        (
            {
                'messageHeader': valid_create_header(),
                # empty body
                'messageBody': {
                    'objectUuid': 'object_uuid',
                    'objectOrganisationRole': valid_create_publisher(),
                },
            }, 'objectFile',
        ),
        (
            {
                'messageHeader': valid_create_header(),
                'messageBody': {
                    'objectUuid': 'object_uuid',
                    # is dict
                    'objectFile': {
                        # missing s3 path
                        'fileName': 'filename',
                        'fileStoragePlatform': {
                            'storagePlatformType': 1,
                        },
                        'fileChecksum': [],
                    },
                    'objectOrganisationRole': valid_create_publisher(),
                },
            }, 'objectFile',
        ),
        (
            {
                # missing message id
                'messageHeader': {
                    'messageType': tasks.MetadataCreateTask.TYPE,
                },
                'messageBody': {
                    'objectUuid': 'object_uuid',
                    'objectFile': valid_create_object_file(),
                    'objectOrganisationRole': valid_create_publisher(),
                },
            }, 'messageId',
        ),
        (
            {
                # missing objectOrganisationRole
                'messageHeader': valid_create_header(),
                'messageBody': {
                    'objectUuid': 'object_uuid',
                    'objectFile': valid_create_object_file(),
                },
            }, 'objectOrganisationRole',
        ),
        (
            {
                'messageHeader': valid_create_header(),
                'messageBody': {
                    'objectUuid': 'object_uuid',
                    'objectFile': valid_create_object_file(),
                },
                # invalid objectOrganisationRole
                'objectOrganisationRole': {
                    'organisation': {
                        'organisationJiscId': 1,
                    },
                    'role': 123,
                },
            }, 'objectOrganisationRole',
        ),
        (
            {
                'messageHeader': valid_create_header(),
                'messageBody': {
                    'objectUuid': 'object_uuid',
                    'objectFile': valid_create_object_file(),
                },
                # invalid objectOrganisationRole
                'objectOrganisationRole': [
                    {'organisation': {'organisationJiscId': 1}, 'role': None},
                ],
            }, 'objectOrganisationRole',
        ),
        (
            {
                'messageHeader': valid_create_header(),
                'messageBody': {
                    'objectUuid': 'object_uuid',
                    'objectFile': [
                        {
                            # missing s3 path
                            'fileName': 'filename',
                            'fileStoragePlatform': {
                                'storagePlatformType': 1,
                            },
                            'fileChecksum': [],
                        },
                    ],
                    'objectOrganisationRole': valid_create_publisher(),
                },
            }, 'fileStorageLocation',
        ),
        (
            {
                'messageHeader': valid_create_header(),
                'messageBody': {
                    'objectUuid': 'object_uuid',
                    'objectFile': [
                        {
                            # no file name
                            'fileStorageLocation': 's3://bucket/path/to/file',
                            'fileStoragePlatform': {
                                'storagePlatformType': 1,
                            },
                            'fileChecksum': [],
                        },
                    ],
                    'objectOrganisationRole': valid_create_publisher(),
                },
            }, 'fileName',
        ),
        (
            {
                'messageHeader': valid_create_header(),
                'messageBody': {
                    'objectUuid': 'object_uuid',
                    'objectFile': [
                        {
                            # wrong s3 path
                            'fileStorageLocation': 'bucket/path/to/file',
                            'fileName': 'filename',
                            'fileStoragePlatform': {
                                'storagePlatformType': 1,
                            },
                            'fileChecksum': [],
                        },
                    ],
                    'objectOrganisationRole': valid_create_publisher(),
                },
            }, 'fileStorageLocation',
        ),
        (
            {
                'messageHeader': valid_create_header(),
                'messageBody': {
                    'objectUuid': 'object_uuid',
                    'objectFile': [
                        {
                            'fileStorageLocation': 's3://bucket/path/to/file',
                            # empty file name
                            'fileName': '',
                            'fileStoragePlatform': {
                                'storagePlatformType': 1,
                            },
                            'fileChecksum': [],
                        },
                    ],
                    'objectOrganisationRole': valid_create_publisher(),
                },
            }, 'fileName',
        ),
        (
            {
                'messageHeader': valid_create_header(),
                'messageBody': {
                    'objectUuid': 'object_uuid',
                    'objectFile': [
                        {
                            'fileStorageLocation': 's3://something/something',
                            'fileName': 'filename',
                            # http type for s3 url
                            'fileStoragePlatform': {
                                'storagePlatformType': 2,
                            },
                            'fileChecksum': [],
                        },
                    ],
                    'objectOrganisationRole': valid_create_publisher(),
                },
            },
            'fileStorageLocation',
        ),
        (
            {
                'messageHeader': valid_create_header(),
                'messageBody': {
                    'objectUuid': 'object_uuid',
                    'objectFile': [
                        {
                            'fileStorageLocation': 'http://something/something',
                            'fileName': 'filename',
                            # http type for s3 url
                            'fileStoragePlatform': {
                                'storagePlatformType': 1,
                            },
                            'fileChecksum': [],
                        },
                    ],
                    'objectOrganisationRole': valid_create_publisher(),
                },
            },
            'fileStorageLocation',
        ),
        (
            {
                'messageHeader': valid_create_header(),
                'messageBody': {
                    'objectUuid': 'object_uuid',
                    'objectFile': [
                        {
                            'fileStorageLocation': 'http://something/something',
                            'fileName': 'filename',
                            'fileStoragePlatform': {
                                'storagePlatformType': 2,
                            },
                            'fileChecksum': [],
                        },
                    ],
                    # no role
                },
            },
            'organisationJiscId',
        ),
        (
            {
                'messageHeader': valid_create_header(),
                'messageBody': {
                    'objectUuid': 'object_uuid',
                    'objectFile': [
                        {
                            'fileStorageLocation': 'http://something/something',
                            'fileName': 'filename',
                            'fileStoragePlatform': {
                                'storagePlatformType': 2,
                            },
                            'fileChecksum': [],
                        },
                    ],
                    'objectOrganisationRole': [
                        {
                            'organisation': {
                                'organisationJiscId': 1,
                            },
                            # Missing role
                        },
                    ],
                },
            },
            'role ID',
        ),
        (
            {
                'messageHeader': valid_create_header(),
                'messageBody': {
                    'objectFile': valid_create_object_file(),
                    'objectOrganisationRole': valid_create_publisher(),
                },
            },
            'objectUuid',
        ),
    ],
)
@mock_preservica_bucket_builder()
def test_metadata_create_task_error(message, error, valid_config):
    with pytest.raises(errors.MalformedBodyError, match=error):
        tasks_parser.record_to_task(to_record(message), valid_config)


@mock_preservica_bucket_builder(jisc_id='jisc', environment='dev')
def test_jisc_tenancy_bucket_selected_in_dev():
    config = Config(
        'dev',
        'https://test_preservica_url',
        'input',
        'invalid',
        'error',
        'eu-west-2',
        organisation_buckets={},
    )
    record = to_record({
        'messageHeader': valid_create_header(),
        'messageBody': {
            'objectUuid': 'object_uuid',
            'objectFile': [
                {
                    'fileStorageLocation': 's3://bucket/path/to/file',
                    'fileName': 'filename',
                    'fileStoragePlatform': {
                        'storagePlatformType': 1,
                    },
                    'fileChecksum': [],
                },
            ],
            'objectOrganisationRole': [{
                'organisation': {
                    'organisationJiscId': 999,
                    'organisationName': 'string',
                    'organisationType': 2,
                    'organisationAddress': 'string',
                },
                'role': 3,
            }],
        },
    })
    task = tasks_parser.record_to_task(record, config)

    assert task.destination_bucket.name == 'com.preservica.rdss.jisc.preservicaadaptor'


@mock_preservica_bucket_builder(jisc_id='jisc', environment='uat')
def test_jisc_tenancy_bucket_selected_in_uat():
    config = Config(
        'uat',
        'https://test_preservica_url',
        'input',
        'invalid',
        'error',
        'eu-west-2',
        organisation_buckets={},
    )
    record = to_record({
        'messageHeader': valid_create_header(),
        'messageBody': {
            'objectUuid': 'object_uuid',
            'objectFile': [
                {
                    'fileStorageLocation': 's3://bucket/path/to/file',
                    'fileName': 'filename',
                    'fileStoragePlatform': {
                        'storagePlatformType': 1,
                    },
                    'fileChecksum': [],
                },
            ],
            'objectOrganisationRole': [{
                'organisation': {
                    'organisationJiscId': 999,
                    'organisationName': 'string',
                    'organisationType': 2,
                    'organisationAddress': 'string',
                },
                'role': 3,
            }],
        },
    })
    task = tasks_parser.record_to_task(record, config)
    assert task.destination_bucket.name == 'com.preservica.rdss.jisc.preservicaadaptor'


@mock_preservica_bucket_builder(jisc_id='999', environment='prod')
def test_institution_tenancy_bucket_selected_in_prod():
    config = Config(
        'prod',
        'https://test_preservica_url',
        'input',
        'invalid',
        'error',
        'eu-west-2',
        organisation_buckets={},
    )
    record = to_record({
        'messageHeader': valid_create_header(),
        'messageBody': {
            'objectUuid': 'object_uuid',
            'objectFile': [
                {
                    'fileStorageLocation': 's3://bucket/path/to/file',
                    'fileName': 'filename',
                    'fileStoragePlatform': {
                        'storagePlatformType': 1,
                    },
                    'fileChecksum': [],
                },
            ],
            'objectOrganisationRole': [{
                'organisation': {
                    'organisationJiscId': 999,
                    'organisationName': 'string',
                    'organisationType': 2,
                    'organisationAddress': 'string',
                },
                'role': 3,
            }],
        },
    })
    task = tasks_parser.record_to_task(record, config)
    assert task.destination_bucket.name == 'com.preservica.rdss.999.preservicaadaptor'


@moto.mock_s3
def test_config_defined_institution_bucket_selected_in_prod():
    bucket_name = 'a.test.bucket'
    create_bucket(bucket_name)
    config = Config(
        'prod',
        'https://test_preservica_url',
        'input',
        'invalid',
        'error',
        'eu-west-2',
        organisation_buckets={
            '999': 's3://' + bucket_name,
        },
    )
    record = to_record({
        'messageHeader': valid_create_header(),
        'messageBody': {
            'objectUuid': 'object_uuid',
            'objectFile': [
                {
                    'fileStorageLocation': 's3://bucket/path/to/file',
                    'fileName': 'filename',
                    'fileStoragePlatform': {
                        'storagePlatformType': 1,
                    },
                    'fileChecksum': [],
                },
            ],
            'objectOrganisationRole': [{
                'organisation': {
                    'organisationJiscId': 999,
                    'organisationName': 'string',
                    'organisationType': 2,
                    'organisationAddress': 'string',
                },
                'role': 3,
            }],
        },
    })
    task = tasks_parser.record_to_task(record, config)
    assert task.destination_bucket.name == bucket_name
