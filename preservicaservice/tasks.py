import abc
import datetime
import logging
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
from .meta import write_object_meta, write_message_meta
from .s3_url import S3Url

logger = logging.getLogger(__name__)


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
    def build(cls, message, config):
        """ Factory method to produce task from json message.

        All validation should happen here

        :param dict message: raw message
        :raise: preservicaservice.errors.MalformedBodyError if any error
        :param config: job environment config
        :type config: preservicaservice.config.Config
        :raise: ValueError if any error
        :return: instance
        :rtype: BaseTask
        """

    @abc.abstractmethod
    def run(self, config):
        """ Run task 
        :param config: job environment config
        :type config: preservicaservice.config.Config
        :return: True if message handled
        :rtype: bool
        """


def require_non_empty_key(message, key1, key2):
    """ Require message to have given non empty key

    :param dict message: source to look at
    :param str key1: 1st key to search
    :param str key2: 2nd key in chain
    :return: value
    :raise: MalformedBodyError in case key is missing
    """
    try:
        value = message[key1][key2]
        if not value:
            raise MalformedBodyError('empty {}'.format(key2))
        return value
    except (KeyError, ValueError, TypeError, AttributeError):
        raise MalformedBodyError('missing {}'.format(key2))


def require_organisation_id(message):
    publishers = require_non_empty_key(
        message,
        'messageBody',
        'objectOrganisationRole',
    )
    try:
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


def require_organisation_role(message):
    publishers = require_non_empty_key(
        message,
        'messageBody',
        'objectOrganisationRole',
    )
    try:
        for publisher in publishers:
            if not isinstance(publisher, dict):
                continue
            value = publisher.get('role', '')
            if not value:
                continue
            value = str(value).strip()
            if not value:
                continue
            return value
        raise MalformedBodyError('missing objectOrganisationRole.role')
    except (KeyError, ValueError, TypeError, AttributeError):
        raise MalformedBodyError('missing objectOrganisationRole.role')


def get_container_name(url):
    """ Derive container name from url

    :param S3Url url: url to look
    :rtype: str or None
    """
    try:
        return url.object_key.split('/')[1].strip() or None
    except IndexError:
        return None


def get_base_archive_path(url):
    """ Derive container name from url

    :param S3Url url: url to look
    :rtype: str or None
    """
    return '/'.join(os.path.dirname(url.object_key).split('/')[1:])


class FileMetadata(object):
    """ File object Metadata, not related to AWS metadata. """

    _required_attrs = ['fileName']

    def __init__(self, **kwargs):
        """
        :param str file_name: file name from message
        """
        for v in FileMetadata._required_attrs:
            if v not in kwargs.keys() or not kwargs.get(v):
                raise MalformedBodyError(
                    'missing {} property from kwargs'.format(v),
                )

        self.fileName = kwargs.get('fileName')

    def generate(self, meta_path):
        """ Generate meta for given target file on given path

        :param str meta_path: file to write
        """
        write_object_meta(meta_path, self.values())

    def values(self):
        """ Get values for tags """
        return self.__dict__.items()


class FileTask(object):
    DEFAULT_FILE_SIZE_LIMIT = 4 * 1000 * 1000 * 1000

    def __init__(
        self, download_url, metadata,
        file_size_limit=DEFAULT_FILE_SIZE_LIMIT,
    ):
        """
        :param S3Url download_url: source url to fetch file
        :param FileMetadata metadata: file related metadata
        :param int file_size_limit: max file size limit
        """
        self.download_url = download_url
        self.metadata = metadata
        self.file_size_limit = file_size_limit
        self.archive_base_path = get_base_archive_path(self.download_url)

    def download(self, download_path):
        """ Download given path from s3 to temp destination.

        :param str download_path: what to download
        """
        url = self.download_url
        bucket = get_bucket(url.bucket_name)
        try:
            bucket.download_file(url.object_key, download_path)
        except botocore.exceptions.ClientError as e:
            raise ResourceNotFoundError(
                'missing file to download {}'.format(e),
            )

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

        contents = (
            (
                download_path, os.path.join(
                    self.archive_base_path,
                    os.path.basename(self.download_url.object_key),
                ),
            ),
            (
                meta_path, os.path.join(
                    self.archive_base_path,
                    '{}.metadata'.format(os.path.basename(
                        self.download_url.object_key,
                    )),
                ),
            ),
        )

        with zipfile.ZipFile(
            zip_path, 'a', compression=zipfile.ZIP_DEFLATED,
        ) as f:
            for src, dst in contents:
                f.write(src, dst)

    def run(self, zip_path):
        """ Prepare and append files to zip bundle
        :param str zip_path: which archive to append data to
        """
        download_path = get_tmp_file()
        meta_path = get_tmp_file()
        try:
            self.metadata.generate(meta_path)
            self.download(download_path)
            self.verify_file_size(download_path)
            self.zip_bundle(zip_path, download_path, meta_path)
        finally:
            for path in (download_path, meta_path):
                if os.path.exists(path):
                    os.unlink(path)


class BaseMetadataCreateTask(BaseTask):
    """
    Creates a package ready for ingest in preservica
    by uploading to the appropriate S3 bucket
    """
    UPLOAD_OVERRIDE = False

    def __init__(
        self, message, file_tasks, upload_url, message_id, role,
        container_name,
    ):
        """
        :param dict message: source message
        :param file_tasks: files to include in bundle wrapped in tasks
        :type file_tasks: list of FileTask
        :param S3Url upload_url: upload url
        :param str message_id: message header id
        :param str role: tag role
        :param str container_name: upload container folder name
        """
        self.message = message
        self.file_tasks = file_tasks
        self.upload_url = upload_url
        self.message_id = str(message_id)
        self.role = role
        self.container_name = container_name

    @classmethod
    def build(cls, message, config):
        """
        :param dict message: raw message
        :param config: job environment config
        :type config: preservicaservice.config.Config
        :return:
        """
        organisation_id = require_organisation_id(message)
        role = require_organisation_role(message)

        upload_url = config.organisation_buckets.get(organisation_id)
        if not upload_url:
            logger.warning(
                'Provided organisation id {} has no configured upload url',
                organisation_id,
            )
            # do nothing to message for unknown organisation
            return None

        message_id = require_non_empty_key(
            message, 'messageHeader', 'messageId',
        ).strip()

        objects = require_non_empty_key(
            message, 'messageBody', 'objectFile',
        )
        if not isinstance(objects, list):
            raise MalformedBodyError('expected objectFile as list')

        file_tasks = list(map(cls.build_file_tasks, objects))
        if not file_tasks:
            raise MalformedBodyError('empty objectFile')

        container_name = get_container_name(file_tasks[0].download_url)
        if not container_name:
            raise MalformedBodyError(
                'First objectFile has no valid url to get container name',
            )

        return cls(
            message,
            file_tasks,
            upload_url,
            message_id,
            role,
            container_name,
        )

    @classmethod
    def build_file_tasks(cls, message):
        url = message.get('fileStorageLocation')
        if not url:
            raise MalformedBodyError(
                'invalid s3 value in fileStorageLocation',
            )
        try:
            download_url = S3Url.parse(url)
        except ValueError:
            raise MalformedBodyError(
                'invalid s3 value in fileStorageLocation',
            )

        try:
            return FileTask(download_url, FileMetadata(**message))
        except Exception as e:
            raise e

    def run(self):
        zip_path = get_tmp_file()
        try:
            # message level meta
            self.bundle_meta(zip_path)

            # per file data
            for task in self.file_tasks:
                task.run(zip_path)

            # target s3 upload
            self.upload_bundle(
                self.upload_url,
                zip_path,
                self.collect_meta(zip_path),
                self.UPLOAD_OVERRIDE,
            )
        finally:
            if os.path.exists(zip_path):
                os.unlink(zip_path)

    def bundle_meta(self, zip_path):
        """ Generate root metadata file for given message

        :param str zip_path: target zip file
        """
        with tempfile.NamedTemporaryFile() as tmp_file:
            meta_path = tmp_file.name
            write_message_meta(meta_path, self.message)

            with zipfile.ZipFile(
                zip_path, 'a', compression=zipfile.ZIP_DEFLATED,
            ) as f:
                f.write(
                    meta_path,
                    '{0}/{0}.metadata'.format(self.container_name),
                )

    def upload_bundle(self, upload_url, zip_path, metadata, override):
        """ Upload given zip to target

        :param upload_url: target s3 folder
        :type upload_url: preservicaservice.s3_url.S3Url
        :param str zip_path: source file
        :param dict metadata: metadata to set on s3 object
        :param bool override: don't fail if file exists
        :return:
        """
        bucket = get_bucket(upload_url.bucket_name)

        key = os.path.join(upload_url.object_key, self.bundle_name)

        if not override:
            if list(bucket.objects.filter(Prefix=key)):
                # TODO: clarify exception
                raise ResourceAlreadyExistsError('object already exists is s3')

        with open(zip_path, 'rb') as f:
            bucket.upload_fileobj(
                f, key,
                ExtraArgs={'Metadata': metadata},
            )

    @property
    def bundle_name(self):
        return '{}.zip'.format(self.message_id)

    def collect_meta(self, zip_file_path):
        """ S3 object metadata

        :param zip_file_path:
        :rtype: dict of (str, str)
        """
        size_uncompressed = 0
        with zipfile.ZipFile(zip_file_path) as f:
            for info in f.infolist():
                size_uncompressed += info.file_size

        # make sure all values are strings
        return {
            'key': self.message_id,
            'bucket': self.upload_url.bucket_name,
            'status': 'ready',
            'name': self.bundle_name,
            'size': str(os.stat(zip_file_path).st_size),
            'size_uncompressed': str(size_uncompressed),
            'createddate': datetime.datetime.now().isoformat(),
            'createdby': self.role,

        }


class MetadataCreateTask(BaseMetadataCreateTask):
    TYPE = 'MetadataCreate'


SUPPORTED_TASKS = (
    MetadataCreateTask,
)
