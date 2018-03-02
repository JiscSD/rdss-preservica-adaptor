import base64
import boto3
import json
import moto
from preservicaservice.processor import (
    RecordProcessor,
)
from preservicaservice.config import (
    Config,
)


def _get_records(client, stream_name):
    shard_id = client.describe_stream(
        StreamName=stream_name,
    )['StreamDescription']['Shards'][0]['ShardId']
    shard_iterator = client.get_shard_iterator(
        StreamName=stream_name,
        ShardId=shard_id,
        ShardIteratorType='TRIM_HORIZON',
    )['ShardIterator']
    result = client.get_records(
        ShardIterator=shard_iterator,
        Limit=1000,
    )
    return result['Records']


@moto.mock_kinesis
def test_record_with_invalid_json_sends_message_to_error_stream():
    client = boto3.client('kinesis', 'eu-west-1')
    client.create_stream(StreamName='error-stream', ShardCount=1)
    config = Config(
        input_stream_name='input-stream',
        input_stream_region='eu-west-1',
        error_stream_name='error-stream',
        error_stream_region='eu-west-1',
        organisation_buckets={},
    )
    processor = RecordProcessor(config=config)

    class FakeRecord():
        data = base64.b64encode(b'{')

    processor.process_records([FakeRecord()], None)

    records = _get_records(client, 'error-stream')
    assert len(records) == 1

    message = json.loads(records[0]['Data'].decode('utf-8'))
    assert message['messageBody']['code'] == 'GENERR007'
    assert 'Malformed JSON' in message['messageBody']['message']


@moto.mock_kinesis
def test_record_with_invalid_rdss_message_sends_message_to_error_stream():
    client = boto3.client('kinesis', 'eu-west-1')
    client.create_stream(StreamName='error-stream', ShardCount=1)
    config = Config(
        input_stream_name='input-stream',
        input_stream_region='eu-west-1',
        error_stream_name='error-stream',
        error_stream_region='eu-west-1',
        organisation_buckets={},
    )
    processor = RecordProcessor(config=config)

    class FakeRecord():
        data = base64.b64encode(b'{"messageHeader":{},"messageBody":{}}')

    processor.process_records([FakeRecord()], None)

    records = _get_records(client, 'error-stream')
    assert len(records) == 1

    message = json.loads(records[0]['Data'].decode('utf-8'))
    assert message['messageBody']['code'] == 'GENERR004'
    assert 'Invalid, missing or corrupt headers' in message['messageBody']['message']


@moto.mock_kinesis
def test_record_unable_to_download_sends_messages_to_error_stream():
    client = boto3.client('kinesis', 'eu-west-1')
    client.create_stream(StreamName='error-stream', ShardCount=1)
    config = Config(
        input_stream_name='input-stream',
        input_stream_region='eu-west-1',
        error_stream_name='error-stream',
        error_stream_region='eu-west-1',
        organisation_buckets={
            44: 's3://some-bucket/',
        },
    )
    processor = RecordProcessor(config=config)

    with open('tests/fixtures/create.json', 'rb') as fixture_file:
        fixture = fixture_file.read()

    class FakeRecord():
        data = base64.b64encode(fixture)

    processor.process_records([FakeRecord()], None)

    records = _get_records(client, 'error-stream')
    assert len(records) == 1

    message = json.loads(records[0]['Data'].decode('utf-8'))
    assert message['messageBody']['code'] == 'GENERR009'
    assert 'Connection refused' in message['messageBody']['details']
