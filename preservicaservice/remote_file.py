import abc
from urllib.parse import urlparse

import boto3
import botocore.exceptions
import requests

from .errors import UnderlyingSystemError


class BaseRemoteFile(abc.ABC):
    """ Wrapper for remote files."""

    def __init__(self, url):
        self.url = url

    @property
    def host(self):
        return urlparse(self.url).netloc

    @property
    def path(self):
        return urlparse(self.url).path.lstrip('/')

    @abc.abstractmethod
    def download(self, download_path):
        """ Download remote file to provided path.
        :param download_path: path on local filesystem to download file to.
        :type download_path: string
        :raise: ResourceNotFoundError if any error
        """


class S3RemoteFile(BaseRemoteFile):
    """ Wrapper for remote S3 files."""

    def get_bucket(self, bucket_name):
        """ Retrieve bucket by name."""
        session = boto3.Session()
        s3 = session.resource('s3')
        return s3.Bucket(bucket_name)

    def download(self, download_path):
        """ Download remote file from S3 to the provided download path."""
        bucket = self.get_bucket(self.host)
        try:
            bucket.download_file(self.path, download_path)
        except botocore.exceptions.ClientError as e:
            raise UnderlyingSystemError(
                'missing file to download resource from S3 {}'.format(e),
            )


class HTTPRemoteFile(BaseRemoteFile):
    """ Wrapper for remote HTTP files."""

    def download(self, download_path):
        """ Download remote file via HTTP to the provided download path."""
        try:
            r = requests.get(self.url, stream=True)
            with open(download_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
        except requests.RequestException as re:
            raise UnderlyingSystemError(
                'unable to download resource via HTTP: {}'.format(re),
            )
