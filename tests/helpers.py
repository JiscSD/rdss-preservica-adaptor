import os
import tempfile
import zipfile
import boto3


def named_temp_file():
    f = tempfile.NamedTemporaryFile(mode='w', delete=False)
    yield f.name
    if os.path.exists(f.name):
        os.unlink(f.name)


def assert_file_exists(path):
    assert os.path.exists(path)


def assert_file_contents(path, contents):
    assert_file_exists(path)
    with open(path) as f:
        assert f.read() == contents


def assert_file_missing(path):
    assert os.path.exists(path) is False


def assert_zip_contains(arc, path, contents=None, partial=None):
    arc = zipfile.ZipFile(arc)
    assert path in arc.namelist(), arc.namelist()
    if contents or partial:
        with arc.open(path) as f:
            file_contents = f.read().decode('utf-8')
            if contents:
                assert file_contents == contents
            else:
                assert partial in file_contents


def create_bucket(bucket_name='bucket'):
    s3 = boto3.resource('s3')
    s3.create_bucket(Bucket=bucket_name)
    return s3.Bucket(bucket_name)


def key_in_bucket1(bucket, key='prefix/foo', contents='bar'):
    bucket.put_object(Key=key, Body=contents)
