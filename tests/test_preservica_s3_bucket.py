import random
import pytest
import mock
import moto
import collections

from Crypto.Cipher import AES
from base64 import b64encode
from preservicaservice.preservica_s3_bucket import (PreservicaBucketAPI, PreservicaS3BucketBuilder)

test_preservica_url = 'https://test_preservica_url'
test_preservica_aes_key = 'aesencryptionkey'


def mock_preservica_encrypt(string):
    """ This is intended to mock the encryption of strings as observed in responses
        from the preservica s3 api, including padding of strings with control chars.
        """
    aes_padding_chars = ['\x01', '\r', '\x0c', '\x08', '\x10']
    padding_size = 16 - (len(string) % 16)
    string += random.choice(aes_padding_chars)*padding_size
    cipher = AES.new(test_preservica_aes_key, AES.MODE_ECB)
    encrypted_string = cipher.encrypt(string)
    return b64encode(encrypted_string)


@pytest.fixture
def mock_preservica_bucketdetails():
    return {
        'aws_access_key_id': 'ATESTACCESSKEYID',
        'aws_secret_access_key': 'ATESTSECRETACCESSKEY',
        'aws_session_token': 'ATESTSESSIONTOKEN',
        'bucket_names': ['a.test.bucket.name', 'a.second.test.bucket.name'],
    }


def mock_preservica_bucketdetails_api_response(*args, **kwargs):
    MockResponse = collections.namedtuple('MockResponse', ['content'])

    mock_bucketdetails = mock_preservica_bucketdetails()

    def _format_siplocations(locations):
        return b''.join([
            b'<sipLocation>%b</sipLocation>' % mock_preservica_encrypt(loc)
            for loc in locations
        ])

    b_names = [(b'bucket_names', _format_siplocations(mock_bucketdetails.pop('bucket_names')))]
    response_data = dict(
        [
            (bytes(key, 'utf-8'), mock_preservica_encrypt(value))
            for key, value in mock_bucketdetails.items()
        ] + b_names,
    )
    response_template = b'"<?xml version=\\"1.0\\" encoding=\\"UTF-16\\"?>' \
                        b'<dataSources><a>%(aws_access_key_id)b</a><b>%(aws_secret_access_key)b</b>'\
                        b'<c>%(aws_session_token)b</c><sipLocations>%(bucket_names)b</sipLocations>'\
                        b'</dataSources>"'
    return MockResponse(content=response_template % response_data)


@mock.patch('requests.get', side_effect=mock_preservica_bucketdetails_api_response)
def test_get_bucket_details(mock_get, mock_preservica_bucketdetails):
    bucket_api = PreservicaBucketAPI(test_preservica_url, test_preservica_aes_key)
    bucket_details = bucket_api.get_bucket_details('test@user.com', 'test_password')
    assert bucket_details == mock_preservica_bucketdetails


@moto.mock_ssm
@moto.mock_s3
def test_get_bucket():
    ssm_client = boto3.client('ssm', region_name='eu-west-2')
    ssm_client.put_parameter(
        Name='',
        Value='',
        Type='SecureString',
        KeyId=kms_key_id,
    )
