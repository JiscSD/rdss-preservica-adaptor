import abc
import os
import tempfile
import zipfile

import boto3
import botocore.exceptions

from .errors import (
    MalformedBodyError,
    ResourceAlreadyExistsError,
    UnderlyingSystemError,
    ResourceNotFoundError
)
from .meta import write_meta
from .s3_url import S3Url


def zip_name_from_url(url):
    return '{}.zip'.format(url.split('/')[-2])


def get_tmp_file():
    return tempfile.NamedTemporaryFile(delete=False).name


def get_bucket(bucket_name):
    session = boto3.Session()
    s3 = session.resource('s3')
    return s3.Bucket(bucket_name)


class BaseTask(abc.ABC):
    """
    Task to run for given input message.
    """
    @classmethod
    @abc.abstractmethod
    def build(cls, message):
        """ Factory method to produce task from json message.

        All validation should happen here

        :param dict message: raw message
        :raise: preservicaservice.errors.MalformedBodyError if any error
        :raise: ValueError if any error
        :return: instance
        :rtype: list of BaseTask
        """

    @abc.abstractmethod
    def run(self, config):
        """ Run task 
        :param config: job environemnt config
        :type config: preservicaservice.config.Config
        :return: True if message handled
        :rtype: bool
        """


def require_non_empty_key_body(message, key):
    """ Require message to have given non empty key

    :param dict message: source to look at
    :param str key: key to search
    :return: value
    :raise: MalformedBodyError in case key is missing
    """
    try:
        value = message['messageBody'][key].strip()
        if not value:
            raise MalformedBodyError('empty {}'.format(key))
        return value
    except (KeyError, ValueError, TypeError, AttributeError):
        raise MalformedBodyError('missing {}'.format(key))


def require_organisation_id(message):
    try:
        publishers = message['messageBody']['objectPublisher']
        for publisher in publishers:
            if not isinstance(publisher, dict):
                continue
            organisation = publisher.get('organisation', {})
            value = organisation.get('organisationJiscId', '')
            if not value:
                continue
            value = str(value).strip()
            if not value:
                continue
            return value
        raise MalformedBodyError('missing organisationJiscId')
    except (KeyError, ValueError, TypeError, AttributeError):
        raise MalformedBodyError('missing organisationJiscId')


class BaseMetadataCreateTask(BaseTask):
    """
    Create and Update tasks are similar, basic implementation of both.
    """
    DEFAULT_FILE_SIZE_LIMIT = 4 * 1000 * 1000 * 1000
    UPLOAD_OVERRIDE = False

    def __init__(self, file_name, download_url, organisation_id,
                 file_size_limit=DEFAULT_FILE_SIZE_LIMIT):
        self.file_name = file_name
        self.download_url = download_url
        self.organisation_id = str(organisation_id)
        self.file_size_limit = file_size_limit

    @classmethod
    def build(cls, message):
        organisation_id = require_organisation_id(message)

        try:
            objects = message['messageBody']['objectFile']
        except (KeyError, AttributeError, ValueError):
            raise MalformedBodyError('expected objectFile as list')
        if not isinstance(objects, list):
            raise MalformedBodyError('expected objectFile as list')

        return list(
            map(lambda obj: cls.build_one(obj, organisation_id), objects)
        )

    @classmethod
    def build_one(cls, message, organisation_id):
        url = message.get('fileStorageLocation')
        if not url:
            raise MalformedBodyError(
                'invalid s3 value in fileStorageLocation'
            )
        try:
            download_url = S3Url.parse(url)
        except ValueError:
            raise MalformedBodyError(
                'invalid s3 value in fileStorageLocation'
            )

        file_name = message.get('fileName')
        if not file_name:
            raise MalformedBodyError('empty fileName')

        return cls(file_name, download_url, organisation_id)

    def run(self, config):
        upload_url = config.organisation_buckets.get(self.organisation_id)
        if not upload_url:
            # do nothing to message for unknown organisation
            return False

        download_path = get_tmp_file()
        meta_path = get_tmp_file()
        zip_path = get_tmp_file()
        try:
            self.generate_meta(meta_path)
            self.download(download_path)
            self.verify_file_size(download_path)
            self.zip_bundle(zip_path, download_path, meta_path)
            self.upload_bundle(
                upload_url,
                zip_path,
                self.UPLOAD_OVERRIDE
            )
        finally:
            for path in (download_path, meta_path, zip_path):
                if os.path.exists(path):
                    os.unlink(path)

        return True

    def download(self, download_path):
        """ Download given path from s3 to temp destination.

        :param str download_path: what to download
        """
        url = self.download_url
        bucket = get_bucket(url.bucket_name)
        try:
            bucket.download_file(url.object_key, download_path)
        except botocore.exceptions.ClientError as e:
            # TODO: define error for that
            raise ResourceNotFoundError(
                'missing file to download {}'.format(e)
            )

    def generate_meta(self, meta_path):
        """ Generate meta for given target file on given path

        :param str meta_path: file to write
        """
        write_meta(meta_path, (('fileName', self.file_name),))

    def verify_file_size(self, path):
        """ Check given path file size limit and raise if not valid.

        :param str path: file to check
        :raise: UnderlyingSystemError if file too big
        """
        size = os.path.getsize(path)
        if size >= self.file_size_limit:
            raise UnderlyingSystemError('')

    def zip_bundle(self, zip_path, download_path, meta_path):
        """ Zip bundle of file and meta to given file

        :param str zip_path: target zip file
        :param str download_path: original file
        :param str meta_path: meta file
        """
        meta_arch_path = os.path.join(
            os.path.dirname(self.download_url.object_key),
            '{}.metadata.xml'.format(os.path.splitext(self.file_name)[0])
        )

        contents = (
            (download_path, self.download_url.object_key),
            (meta_path, meta_arch_path)
        )

        with zipfile.ZipFile(zip_path, 'w') as f:
            for src, dst in contents:
                f.write(src, dst)

    def upload_bundle(self, upload_url, zip_path, override):
        """ Upload given zip to target

        :param upload_url: target s3 folder
        :type upload_url: preservicaservice.s3_url.S3Url
        :param str zip_path: source file
        :param bool override: don't fail if file exists
        :return:
        """
        bucket = get_bucket(upload_url.bucket_name)

        object_name = zip_name_from_url(self.download_url.object_key)
        key = os.path.join(upload_url.object_key, object_name)

        if not override:
            if list(bucket.objects.filter(Prefix=key)):
                # TODO: clarify exception
                raise ResourceAlreadyExistsError('object already exists is s3')

        with open(zip_path, 'rb') as f:
            bucket.upload_fileobj(f, key)


class MetadataCreateTask(BaseMetadataCreateTask):
    TYPE = 'MetadataCreate'


class MetadataUpdateTask(BaseMetadataCreateTask):
    TYPE = 'MetadataUpdate'
    UPLOAD_OVERRIDE = True


class MetadataDeleteTask(BaseTask):
    """ Deletion task """
    TYPE = 'MetadataDelete'

    def __init__(self, delete_url):
        """
        :param delete_url: target s3 url
        :type delete_url: preservicaservice.s3_url.S3Url
        """
        self.delete_url = delete_url

    @classmethod
    def build(cls, message):
        url = require_non_empty_key_body(message, 'objectUid')
        try:
            delete_url = S3Url.parse(url)
        except ValueError:
            raise MalformedBodyError('invalid s3 value in objectUid')

        return [cls(delete_url)]

    def run(self, config):
        bucket = get_bucket(self.delete_url.bucket_name)
        bucket.delete_objects(
            Delete={
                'Objects': [
                    {
                        'Key': self.delete_url.object_key,
                    },
                ],
                'Quiet': True
            },
        )


SUPPORTED_TASKS = (
    MetadataCreateTask,
    MetadataUpdateTask,
    MetadataDeleteTask,
)
