import base64
import boto3
import hashlib
import json
import moto
import pytest
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
    client.create_stream(StreamName='invalid-stream', ShardCount=1)
    config = Config(
        environment='test',
        preservica_base_url='https://test_preservica_url',
        input_stream_name='input-stream',
        invalid_stream_name='invalid-stream',
        error_stream_name='error-stream',
        adaptor_aws_region='eu-west-1',
        organisation_buckets={},
    )
    processor = RecordProcessor(config=config)

    class FakeRecord():
        data = base64.b64encode(b'{')

    processor.process_records([FakeRecord()], None)

    records = _get_records(client, 'error-stream')
    assert len(records) == 1

    message = json.loads(records[0]['Data'].decode('utf-8'))
    assert message['messageHeader']['errorCode'] == 'GENERR007'
    assert 'Malformed JSON' in message['messageHeader']['errorDescription']
    assert set(message['messageHeader'].keys()) == {
        'errorCode', 'errorDescription', 'errorDescription', 'messageHistory', 'messageType',
    }


@moto.mock_kinesis
def test_record_with_invalid_rdss_message_sends_message_to_invalid_stream():
    client = boto3.client('kinesis', 'eu-west-1')
    client.create_stream(StreamName='error-stream', ShardCount=1)
    client.create_stream(StreamName='invalid-stream', ShardCount=1)
    config = Config(
        environment='test',
        preservica_base_url='https://test_preservica_url',
        input_stream_name='input-stream',
        invalid_stream_name='invalid-stream',
        error_stream_name='error-stream',
        adaptor_aws_region='eu-west-1',
        organisation_buckets={},
    )
    processor = RecordProcessor(config=config)

    class FakeRecord():
        data = base64.b64encode(b'{"messageHeader":{},"messageBody":{}}')

    processor.process_records([FakeRecord()], None)

    records = _get_records(client, 'invalid-stream')
    assert len(records) == 1

    message = json.loads(records[0]['Data'].decode('utf-8'))
    assert message['messageHeader']['errorCode'] == 'GENERR004'
    assert 'Invalid, missing or corrupt headers' in message['messageHeader']['errorDescription']
    assert set(message['messageHeader'].keys()) == {
        'errorCode', 'errorDescription', 'errorDescription', 'messageHistory', 'messageType',
    }

# TODO Remove to re-enable checksum and fsize validation


@pytest.mark.skip(reason='checksum validation disabled to allow processing of prod willow messages')
@moto.mock_s3
@moto.mock_kinesis
def test_record_with_invalid_checksum_sends_message_to_invalid_stream():
    s3_resource = boto3.resource('s3', region_name='us-east-1')
    s3_resource.create_bucket(Bucket='the-download-bucket')
    obj = s3_resource.Object('the-download-bucket', 'the-download-key')
    obj.put(Body=b'Some contents')

    client = boto3.client('kinesis', 'eu-west-1')
    client.create_stream(StreamName='error-stream', ShardCount=1)
    client.create_stream(StreamName='invalid-stream', ShardCount=1)
    config = Config(
        environment='test',
        preservica_base_url='https://test_preservica_url',
        input_stream_name='input-stream',
        invalid_stream_name='invalid-stream',
        error_stream_name='error-stream',
        adaptor_aws_region='eu-west-1',
        organisation_buckets={
            '98765': 's3://the-upload-bucket/',
        },
    )
    processor = RecordProcessor(config=config)

    class FakeRecord():
        data = base64.b64encode(json.dumps({
            'messageHeader': {
                'messageType': 'MetadataCreate',
                'messageId': 'the-message-id',
            },
            'messageBody': {
                'objectUuid': 'the-id',
                'objectOrganisationRole': [{
                    'organisation': {
                        'organisationJiscId': 98765,
                    },
                    'role': 'some-role-id',
                }],
                'objectFile': [{
                    # "fileUuid": "a3290140-18e1-506e-abec-61e31791e749",
                    'fileStorageLocation': 's3://the-download-bucket/the-download-key',
                    'fileStoragePlatform': {
                        'storagePlatformType': 1,
                    },
                    'fileName': 'the file name',
                    'fileChecksum': [{
                        'checksumType': 1,
                        'checksumValue': 'definitely-not-the-checksum',
                    }],
                }],
            },
        }).encode('utf-8'))

    processor.process_records([FakeRecord()], None)

    records = _get_records(client, 'invalid-stream')
    message = json.loads(records[0]['Data'].decode('utf-8'))
    assert message['messageHeader']['errorCode'] == 'APPERRMET004'
    assert 'A file did not match its checksum' in message['messageHeader']['errorDescription']


@moto.mock_s3
@moto.mock_kinesis
def test_record_with_valid_checksum_does_not_send_message_to_invalid_stream():
    s3_resource = boto3.resource('s3', region_name='us-east-1')
    s3_resource.create_bucket(Bucket='the-download-bucket')
    obj = s3_resource.Object('the-download-bucket', 'the-download-key')
    obj.put(Body=b'Some contents')
    checksum = hashlib.md5()
    checksum.update(b'Some contents')

    client = boto3.client('kinesis', 'eu-west-1')
    client.create_stream(StreamName='error-stream', ShardCount=1)
    client.create_stream(StreamName='invalid-stream', ShardCount=1)
    config = Config(
        environment='test',
        preservica_base_url='https://test_preservica_url',
        input_stream_name='input-stream',
        invalid_stream_name='invalid-stream',
        error_stream_name='error-stream',
        adaptor_aws_region='eu-west-1',
        organisation_buckets={
            '98765': 's3://the-upload-bucket/',
        },
    )
    processor = RecordProcessor(config=config)

    class FakeRecord():
        data = base64.b64encode(json.dumps({
            'messageHeader': {
                'messageType': 'MetadataCreate',
                'messageId': 'the-message-id',
            },
            'messageBody': {
                'objectUuid': 'the-id',
                'objectOrganisationRole': [{
                    'organisation': {
                        'organisationJiscId': 98765,
                    },
                    'role': 'some-role-id',
                }],
                'objectFile': [{
                    # "fileUuid": "a3290140-18e1-506e-abec-61e31791e749",
                    'fileStorageLocation': 's3://the-download-bucket/the-download-key',
                    'fileStoragePlatform': {
                        'storagePlatformType': 1,
                    },
                    'fileName': 'the file name',
                    'fileChecksum': [{
                        'checksumType': 1,
                        'checksumValue': checksum.hexdigest(),
                    }],
                }],
            },
        }).encode('utf-8'))

    processor.process_records([FakeRecord()], None)

    records = _get_records(client, 'invalid-stream')
    assert len(records) == 0


@moto.mock_kinesis
def test_record_unable_to_download_sends_messages_to_error_stream():
    client = boto3.client('kinesis', 'eu-west-1')
    client.create_stream(StreamName='error-stream', ShardCount=1)
    client.create_stream(StreamName='invalid-stream', ShardCount=1)
    config = Config(
        environment='test',
        preservica_base_url='https://test_preservica_url',
        input_stream_name='input-stream',
        invalid_stream_name='invalid-stream',
        error_stream_name='error-stream',
        adaptor_aws_region='eu-west-1',
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
    assert message['messageHeader']['errorCode'] == 'GENERR011'
    assert 'Resource not found' in message['messageHeader']['errorDescription']
    assert set(message['messageHeader'].keys()) == {
        'errorCode', 'errorDescription', 'errorDescription',
        'messageClass', 'messageId', 'messageHistory', 'messageType',
    }
    assert set(message['messageBody'].keys()) == {
        'objectFile', 'objectUuid', 'objectOrganisationRole', 'objectTitle',
    }


@moto.mock_s3
@moto.mock_kinesis
def test_record_samvera_prod_processes():
    s3_resource = boto3.resource('s3', region_name='us-east-1')
    s3_resource.create_bucket(Bucket='some-bucket')
    client = boto3.client('kinesis', 'eu-west-1')
    client.create_stream(StreamName='error-stream', ShardCount=1)
    client.create_stream(StreamName='invalid-stream', ShardCount=1)
    config = Config(
        environment='test',
        preservica_base_url='https://test_preservica_url',
        input_stream_name='input-stream',
        invalid_stream_name='invalid-stream',
        error_stream_name='error-stream',
        adaptor_aws_region='eu-west-1',
        organisation_buckets={
            747: 's3://some-bucket/',
        },
    )
    processor = RecordProcessor(config=config)

    with open('tests/fixtures/create_samvera_0.0.1-SNAPSHOT.json', 'rb') as fixture_file:
        fixture = fixture_file.read()

    class FakeRecord():
        data = base64.b64encode(fixture)

    processor.process_records([FakeRecord()], None)

    records = _get_records(client, 'error-stream')
    assert len(records) == 0


@moto.mock_kinesis
def test_record_figshare_prod_processes():
    client = boto3.client('kinesis', 'eu-west-1')
    client.create_stream(StreamName='error-stream', ShardCount=1)
    client.create_stream(StreamName='invalid-stream', ShardCount=1)
    config = Config(
        environment='test',
        preservica_base_url='https://test_preservica_url',
        input_stream_name='input-stream',
        invalid_stream_name='invalid-stream',
        error_stream_name='error-stream',
        adaptor_aws_region='eu-west-1',
        organisation_buckets={
            89: 's3://some-bucket/',
        },
    )
    processor = RecordProcessor(config=config)

    with open('tests/fixtures/create_figshare_1.json', 'rb') as fixture_file:
        fixture = fixture_file.read()

    class FakeRecord():
        data = base64.b64encode(fixture)

    processor.process_records([FakeRecord()], None)

    records = _get_records(client, 'error-stream')
    assert len(records) == 0
