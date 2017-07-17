import base64
import json
from collections import namedtuple

import pytest

from preservicaservice import errors
from preservicaservice import tasks
from preservicaservice import tasks_parser

Record = namedtuple('Record', 'data')


def to_base64(value, encoding='utf-8'):
    value = base64.b64encode(bytes(value, encoding))
    return str(value, 'utf-8')


def to_record(data):
    return Record(to_base64(json.dumps(data)))


@pytest.mark.parametrize('data, error', [
    (None, errors.MalformedJsonBodyError),
    (to_base64('abc', encoding='koi8-r'), errors.MalformedJsonBodyError),
    (to_base64('[1,2]'), errors.MalformedJsonBodyError),
])
def test_decode_record_error(data, error):
    with pytest.raises(error):
        tasks_parser.decode_record(Record(str(data)))


@pytest.mark.parametrize('data, value', [
    (to_base64('{"a": "b"}'), {'a': 'b'}),
])
def test_decode_record(data, value):
    assert tasks_parser.decode_record(Record(str(data))) == value


@pytest.mark.parametrize('message, error', [
    ({}, errors.MalformedHeaderError),
    ({'messageHeader': {}}, errors.MalformedHeaderError),
    ({'messageHeader': {'messageType': []}}, errors.MalformedHeaderError),
    ({'messageHeader': {'messageType': 'abc'}},
     errors.UnsupportedMessageTypeError),
])
def test_create_supported_task_error(message, error):
    with pytest.raises(error):
        tasks_parser.create_supported_tasks(message)


def test_metadata_create_task():
    record = to_record({
        'messageHeader': {
            'messageType': tasks.MetadataCreateTask.TYPE
        },
        'messageBody': {
            'objectFile': [
                {
                    'fileStorageLocation': 's3://bucket/path/to/file',
                    'fileName': 'filename',
                },
                {
                    'fileStorageLocation': 's3://bucket/path/to/file2',
                    'fileName': 'filename2',
                }
            ],
        }
    })
    tasks_ = tasks_parser.record_to_task(record)
    assert isinstance(tasks_, list)
    assert len(tasks_) == 2

    task = tasks_[0]
    assert isinstance(task, tasks.MetadataCreateTask)
    assert task.download_url.url == 's3://bucket/path/to/file'
    assert task.file_name == 'filename'

    task = tasks_[1]
    assert isinstance(task, tasks.MetadataCreateTask)
    assert task.download_url.url == 's3://bucket/path/to/file2'
    assert task.file_name == 'filename2'


@pytest.mark.parametrize('body', [
    {},
    {'objectFile': {
        'fileName': 'filename',
    }},
    {'objectFile': {
        'fileStorageLocation': 's3://bucket/path/to/file',
    }},
    {'objectFile': {
        'fileStorageLocation': 'bucket/path/to/file',
        'fileName': 'filename',
    }},
    {'objectFile': {
        'fileStorageLocation': 's3://bucket/path/to/file',
        'fileName': '',
    }},
])
def test_metadata_create_task_error(body):
    record = to_record({
        'messageHeader': {
            'messageType': tasks.MetadataCreateTask.TYPE
        },
        'messageBody': body
    })
    with pytest.raises(errors.MalformedBodyError):
        tasks_parser.record_to_task(record)


def test_metadata_update_task():
    record = to_record({
        'messageHeader': {
            'messageType': tasks.MetadataUpdateTask.TYPE
        },
        'messageBody': {
            'objectFile': [
                {
                    'fileStorageLocation': 's3://bucket/path/to/file',
                    'fileName': 'filename',
                },
                {
                    'fileStorageLocation': 's3://bucket/path/to/file2',
                    'fileName': 'filename2',
                }
            ],
        }
    })
    tasks_ = tasks_parser.record_to_task(record)
    assert isinstance(tasks_, list)
    assert len(tasks_) == 2

    task = tasks_[0]
    assert isinstance(task, tasks.MetadataUpdateTask)
    assert task.download_url.url == 's3://bucket/path/to/file'
    assert task.file_name == 'filename'

    task = tasks_[1]
    assert isinstance(task, tasks.MetadataUpdateTask)
    assert task.download_url.url == 's3://bucket/path/to/file2'
    assert task.file_name == 'filename2'


@pytest.mark.parametrize('body', [
    {},
    {'objectFile': {
        'fileName': 'filename',
    }},
    {'objectFile': {
        'fileStorageLocation': 's3://bucket/path/to/file',
    }},
    {'objectFile': {
        'fileStorageLocation': 'bucket/path/to/file',
        'fileName': 'filename',
    }},
    {'objectFile': {
        'fileStorageLocation': 's3://bucket/path/to/file',
        'fileName': '',
    }},
])
def test_metadata_update_task_error(body):
    record = to_record({
        'messageHeader': {
            'messageType': tasks.MetadataUpdateTask.TYPE
        },
        'messageBody': body
    })
    with pytest.raises(errors.MalformedBodyError):
        tasks_parser.record_to_task(record)


def test_metadata_delete_task():
    record = to_record({
        'messageHeader': {
            'messageType': tasks.MetadataDeleteTask.TYPE
        },
        'messageBody': {
            'objectUid': 's3://bucket/path/to/file',
        }
    })
    tasks_ = tasks_parser.record_to_task(record)
    assert isinstance(tasks_, list)
    assert len(tasks_) == 1
    task = tasks_[0]
    assert isinstance(task, tasks.MetadataDeleteTask)
    assert task.delete_url.url == 's3://bucket/path/to/file'


@pytest.mark.parametrize('body', [
    {
        'objectUid': '',
    },
    {
        'objectUid': 'http://bucket/path/to/file',
    },
])
def test_metadata_delete_task_error(body):
    record = to_record({
        'messageHeader': {
            'messageType': tasks.MetadataDeleteTask.TYPE
        },
        'messageBody': body
    })
    with pytest.raises(errors.MalformedBodyError):
        tasks_parser.record_to_task(record)
