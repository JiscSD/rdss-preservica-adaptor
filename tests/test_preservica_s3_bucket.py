import random
import functools
import boto3
import pytest
import mock
import moto
import collections
import contextlib

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
    bstring = bytes(string, 'utf-8')
    aes_key = bytes(test_preservica_aes_key, 'utf-8')
    cipher = AES.new(aes_key, AES.MODE_ECB)
    encrypted_string = cipher.encrypt(bstring)
    return b64encode(encrypted_string)


def mock_preservica_bucketdetails(jisc_id='jisc'):
    """ Format a dict that duplicates the return value of a 
        PreservicaBucketAPI.get_bucket_details() response.
        """
    return {
        'aws_access_key_id': 'ATESTACCESSKEYID',
        'aws_secret_access_key': 'ATESTSECRETACCESSKEY',
        'aws_session_token': 'ATESTSESSIONTOKEN',
        'bucket_names': [
            'a.test.bucket.name',
            'com.preservica.rdss.{}.preservicaadaptor'.format(jisc_id),
            'a.second.test.bucket.name',
        ],
    }


def mock_preservica_bucketdetails_api_response(jisc_id='jisc'):
    """ Mocks a `requests` response object with the `.content` property
        as a recreation of the responses from preservica's bucketdetails endpoint. 
        """
    MockResponse = collections.namedtuple('MockResponse', ['content'])

    mock_bucketdetails = mock_preservica_bucketdetails(jisc_id)

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
    return lambda *args, **kwargs: MockResponse(content=response_template % response_data)


def mock_preservica_bucket_builder(jisc_id='jisc', environment='test'):
    """ A decorator that spins up mocking for the AWS and Preservica API's that 
        the PreservicaS3BucketBuilder class calls upon. 
        """

    def setup_ssm():
        kms_client = boto3.client('kms', region_name='eu-west-2')
        ssm_client = boto3.client('ssm', region_name='eu-west-2')
        kms_key_id = kms_client.create_key()['KeyMetadata']['KeyId']
        ssm_client.put_parameter(
            Name='preservica-adaptor-{}-api-decryption-key'.format(environment),
            Value='aesencryptionkey',
            Type='SecureString',
            KeyId=kms_key_id,
        )

        ssm_client.put_parameter(
            Name='preservica-adaptor-{}-{}-preservica-user'.format(jisc_id, environment),
            Value='test@user.com',
            Type='SecureString',
            KeyId=kms_key_id,
        )

        ssm_client.put_parameter(
            Name='preservica-adaptor-{}-{}-preservica-password'.format(jisc_id, environment),
            Value='test_password',
            Type='SecureString',
            KeyId=kms_key_id,
        )

    def setup_s3():
        s3_client = boto3.client('s3', region_name='eu-west-2')
        bucket_name = 'com.preservica.rdss.{}.preservicaadaptor'.format(jisc_id)
        test_bucket = s3_client.create_bucket(Bucket=bucket_name)

    mocking_managers = [
        (moto.mock_s3, [], {}),
        (moto.mock_ssm, [], {}),
        (moto.mock_kms, [], {}),
        (
            mock.patch,
            ['preservicaservice.preservica_s3_bucket.PreservicaBucketAPI._get_encrypted_bucket_details'],
            {'side_effect': mock_preservica_bucketdetails_api_response(jisc_id)},
        ),
    ]

    def decorator(func, *args, **kwargs):
        # `wraps` preserves function info for decorated function e.g. __name__
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # This allows the setup of multiple context managers without lots of nested `withs`
            with contextlib.ExitStack() as stack:
                [
                    stack.enter_context(f(*f_args, **f_kwargs))
                    for f, f_args, f_kwargs in mocking_managers
                ]
                setup_ssm()
                setup_s3()
                return func(*args, **kwargs)
        return wrapper
    return decorator


@mock.patch('requests.get', side_effect=mock_preservica_bucketdetails_api_response())
def test_get_bucket_details(mock_get):
    bucket_api = PreservicaBucketAPI(test_preservica_url, test_preservica_aes_key)
    bucket_details = bucket_api.get_bucket_details('test@user.com', 'test_password')
    assert bucket_details == mock_preservica_bucketdetails()


@mock_preservica_bucket_builder()
def test_get_bucket():
    bucket_builder = PreservicaS3BucketBuilder(test_preservica_url, 'test', 'eu-west-2')
    preservica_bucket = bucket_builder.get_bucket('jisc')
    bucket_name = 'com.preservica.rdss.jisc.preservicaadaptor'
    assert bucket_name == preservica_bucket.name
