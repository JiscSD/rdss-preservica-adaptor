import moto
import pytest

from preservicaservice import tasks
from preservicaservice.config import Config
from preservicaservice.s3_url import S3Url
from .helpers import create_bucket


@pytest.fixture
def task():
    yield tasks.MetadataDeleteTask(S3Url('s3://bucket/prefix/foo'))


@pytest.fixture
def config():
    return Config(
        'input',
        'eu-west-1',
        'error',
        'eu-west-1',
        's3://upload/to'
    )


@moto.mock_s3
def test_delete_existing(task, config):
    bucket = create_bucket()
    bucket.put_object(Key='prefix/foo', Body='bar')
    task.run(config)
    assert 'prefix/foo' not in list(bucket.objects.all())


@moto.mock_s3
def test_delete_missing(task, config):
    bucket = create_bucket()
    task.run(config)
    assert 'prefix/foo' not in list(bucket.objects.all())
