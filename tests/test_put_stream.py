import boto3
import moto
import pytest

from preservicaservice import put_stream
from preservicaservice.errors import (
    MaxMessageSendTriesError,
    ResourceNotFoundError
)


def test_exponential_generator():
    expected = [200, 400, 800, 1600, 3200, 6400, 12800, 25600, 51200, 102400]
    for i, actual in enumerate(
            put_stream.exponential_generator('x', ValueError, multiplier=100),
    ):
        assert actual == expected.pop(0)
        if not expected:
            break


def test_exponential_generator_raises():
    with pytest.raises(ValueError, match='x'):
        list(put_stream.exponential_generator('x', ValueError))


@moto.mock_kinesis
def test_put():
    client = boto3.client('kinesis', 'us-west-1')
    client.create_stream(StreamName='in', ShardCount=1)

    put_stream.PutStream('in', 'us-west-1').put('{abc}')

    desc = client.describe_stream(StreamName='in')
    shard_id = desc['StreamDescription']['Shards'][0]['ShardId']

    shard_iterator = client.get_shard_iterator(
        StreamName='in',
        ShardId=shard_id,
        ShardIteratorType='TRIM_HORIZON',
    )

    resp = client.get_records(
        ShardIterator=shard_iterator['ShardIterator'],
        Limit=10,
    )

    records = resp['Records']
    actual = list(map(lambda x: x['Data'], records))
    assert actual == [b'{abc}']


@moto.mock_kinesis
def test_init_missing_stream():
    with pytest.raises(ResourceNotFoundError):
        put_stream.PutStream('in', 'us-west-1', number_of_tries=1)


@moto.mock_kinesis
def test_put_or_fail_missing_stream():
    client = boto3.client('kinesis', 'us-west-1')
    client.create_stream(StreamName='in', ShardCount=1)
    stream = put_stream.PutStream('in', 'us-west-1', number_of_tries=1)
    client.delete_stream(StreamName='in')
    with pytest.raises(
        MaxMessageSendTriesError,
        match='gave up writing data to stream in after 1 tries',
    ):
        stream.put_or_fail('{abc}')


@moto.mock_kinesis
def test_put_missing_stream():
    client = boto3.client('kinesis', 'us-west-1')
    client.create_stream(StreamName='in', ShardCount=1)
    stream = put_stream.PutStream('in', 'us-west-1', number_of_tries=1)
    client.delete_stream(StreamName='in')
    stream.put('{abc}')
