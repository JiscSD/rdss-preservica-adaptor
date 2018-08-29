import abc
import datetime
import hashlib
import base64
import logging
import os
import tempfile
import zipfile
import boto3

from .errors import (
    MalformedBodyError,
    ResourceAlreadyExistsError,
    UnderlyingSystemError,
    InvalidChecksumError,
)
from .meta import write_object_meta, write_message_meta
from .remote_urls import S3RemoteUrl, HTTPRemoteUrl
from .preservica_s3_bucket import PreservicaS3BucketBuilder

logger = logging.getLogger(__name__)


def get_tmp_file():
    return tempfile.NamedTemporaryFile(delete=False).name


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


def first_org_id_from_org_roles(org_roles):
    """ Return first Jisc ID found in an objectOrganisationRole."""
    for role in org_roles:
        if not isinstance(role, dict):
            continue
        org = role.get('organisation')
        if not isinstance(org, dict):
            continue
        org_id = org.get('organisationJiscId')
        if not org_id:
            continue
        return str(org_id).strip()


def first_org_id_from_person_roles(person_roles):
    """ Return first Jisc ID found in an objectPersonRole."""
    for role in person_roles:
        if not isinstance(role, dict):
            continue
        person = role.get('person')
        if not isinstance(person, dict):
            continue
        org_unit = person.get('personOrganisationUnit', {})
        if not isinstance(org_unit, dict):
            continue
        org = org_unit.get('organisation', {})
        org_id = org.get('organisationJiscId')
        if not org_id:
            continue
        return str(org_id).strip()


def require_organisation_id(message):
    """ Retrieve Jisc ID from message payload or raise MalformedBodyError."""
    message_body = message.get('messageBody')
    if not isinstance(message_body, dict):
        raise MalformedBodyError('messageBody is not a dict.')

    org_roles = message_body.get('objectOrganisationRole', [])
    value = first_org_id_from_org_roles(org_roles)
    if value:
        return value

    person_roles = message_body.get('objectPersonRole', [])
    value = first_org_id_from_person_roles(person_roles)
    if value:
        return value

    raise MalformedBodyError(
        'Unable to determine organisationJiscId org ID. '
        'Missing {0} or {1} fields?'.format(
            'objectOrganisationRole',
            'objectPersonRole',
        ),
    )


def first_role_id_in_roles(roles):
    """ Return the first role ID found in list of roles."""
    for role in roles:
        if not isinstance(role, dict):
            continue
        role_id = role.get('role')
        if not role_id:
            continue
        return str(role_id).strip()


def require_organisation_role(message):
    """ Retrieve role ID from message payload or raise exception."""
    message_body = message.get('messageBody')
    if not isinstance(message_body, dict):
        raise MalformedBodyError('messageBody is not a dict.')

    org_roles = message_body.get('objectOrganisationRole', [])
    value = first_role_id_in_roles(org_roles)
    if value:
        return value

    person_roles = message_body.get('objectPersonRole', [])
    value = first_role_id_in_roles(person_roles)
    if value:
        return value

    raise MalformedBodyError(
        'Unable to determine role ID. '
        'Missing {0} or {1} fields?'.format(
            'objectOrganisationRole',
            'objectPersonRole',
        ),
    )


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
    DEFAULT_FILE_SIZE_LIMIT = 5 * 1024 * 1024 * 1024 + 1

    def __init__(
        self, remote_file, metadata, message_id, object_id, file_checksum,
        file_size_limit=DEFAULT_FILE_SIZE_LIMIT,
    ):
        """
        :param remote_file: remote_file.BaseRemoteFile
        :param FileMetadata metadata: file related metadata
        :param int file_size_limit: max file size limit
        """
        self.remote_file = remote_file
        self.metadata = metadata
        self.file_size_limit = file_size_limit
        self.message_id = message_id
        self.archive_base_path = object_id
        self.file_checksum = file_checksum

    def download(self, download_path):
        """ Download given path from s3 to temp destination.

        :param str download_path: what to download
        """
        self.remote_file.download(download_path)

    def verify_file_size(self, path):
        """ Check given path file size limit and raise if not valid.

        :param str path: file to check
        :raise: UnderlyingSystemError if file too big
        """
        size = os.path.getsize(path)
        if size >= self.file_size_limit:
            raise UnderlyingSystemError('')

    def verify_checksums(self, path):
        """ Check given path checksums and raise if not valid.

        :param str path: file to check
        :raise: InvalidChecksumError if file too big
        """

        # Map from RDSS checksumType, which is an integer designed to not change, to a
        # string type that is used internally here. The string values here do need to
        # match the names in hashlib, but are independent of anything in the messsage
        # API spec
        CHECKSUM_TYPES = {
            1: 'md5',
            2: 'sha256',
        }
        checksums = [
            {
                'type': CHECKSUM_TYPES[checksum_rdss['checksumType']],
                'expected': checksum_rdss['checksumValue'],
                'calculated': getattr(hashlib, CHECKSUM_TYPES[checksum_rdss['checksumType']])(),
            } for checksum_rdss in self.file_checksum
        ]

        if not checksums:
            logger.debug('No checksums received. Skipping verification')
            return

        # We avoid reading the file into memory at once, and we only
        # iterate through the file contents once, even if multiple checkums
        # received
        def read_chunks(file):
            while True:
                chunk = file.read(2048)
                if not chunk:
                    break
                yield chunk

        logger.debug('Opening %s to find its checksums', path)

        with open(path, 'rb') as file:
            for chunk in read_chunks(file):
                for checksum in checksums:
                    checksum['calculated'].update(chunk)

        logger.debug('Calculated checksums %s', checksums)

        non_matching_checksums = [
            checksum for checksum in checksums
            if checksum['expected'] != checksum['calculated'].hexdigest()
        ]

        if non_matching_checksums:
            logger.debug(
                'Found non matching checksums %s',
                non_matching_checksums,
            )
            raise InvalidChecksumError(
                'Found non matching checksums: {}'.format(
                    non_matching_checksums,
                ),
            )

    def zip_bundle(self, zip_path, download_path, meta_path):
        """ Zip bundle of file and meta to given file

        :param str zip_path: target zip file
        :param str download_path: original file
        :param str meta_path: meta file
        """
        contents = (
            (
                download_path,
                os.path.join(
                    self.archive_base_path,
                    os.path.basename(self.remote_file.name),
                ),
            ),
            (
                meta_path,
                os.path.join(
                    self.archive_base_path,
                    '{}.metadata'.format(os.path.basename(
                        self.remote_file.name,
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
            self.verify_checksums(download_path)
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
        self, message, file_tasks, destination_bucket, message_id, role, object_id,
    ):
        """
        :param dict message: source message
        :param file_tasks: files to include in bundle wrapped in tasks
        :type file_tasks: list of FileTask
        :param boto3.S3.Bucket: destination_bucket
        :param str message_id: message header id
        :param str role: tag role
        """
        self.message = message
        self.file_tasks = file_tasks
        self.destination_bucket = destination_bucket
        self.message_id = message_id
        self.object_id = object_id
        self.role = role

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
        if upload_url:
            session = boto3.Session()
            s3 = session.resource('s3')
            destination_bucket = s3.Bucket(upload_url.host)
        else:
            if config.environment != 'prod':
                bucket_jisc_id = 'jisc'
            else:
                bucket_jisc_id = organisation_id
            bucket_builder = PreservicaS3BucketBuilder(
                config.preservica_base_url,
                config.environment,
                config.adaptor_aws_region,
            )
            destination_bucket = bucket_builder.get_bucket(bucket_jisc_id)
            if not destination_bucket:
                logger.warning(
                    'No Preservica S3 bucket available for %s', bucket_jisc_id,
                )
                return None

        message_id = require_non_empty_key(
            message, 'messageHeader', 'messageId',
        ).strip()

        try:
            objects = message['messageBody']['objectFile']
        except KeyError:
            raise MalformedBodyError('missing objectFile')

        object_id = require_non_empty_key(message, 'messageBody', 'objectUuid')
        if not isinstance(objects, list):
            raise MalformedBodyError('expected objectFile as list')

        file_tasks = []
        for obj in objects:
            file_tasks.append(cls.build_file_task(obj, message_id, object_id))

        return cls(
            message,
            file_tasks,
            destination_bucket,
            message_id,
            role,
            object_id,
        )

    @classmethod
    def build_file_task(cls, object_file, message_id, object_id):
        try:
            url = object_file['fileStorageLocation']
            file_name = object_file['fileName']
            storage_platform = object_file['fileStoragePlatform']
            storage_type = storage_platform['storagePlatformType']
            file_checksum = object_file['fileChecksum']

        except (TypeError, KeyError) as exception:
            raise MalformedBodyError(
                'Unable to parse file: {}'.format(str(exception)),
            )

        try:
            storage_types = {
                1: S3RemoteUrl,
                2: HTTPRemoteUrl,
            }
            remote_file_class = storage_types[storage_type]
        except KeyError:
            raise MalformedBodyError(
                'Unsupported storagePlatformType ({})'.format(storage_type),
            )

        try:
            remote_file = remote_file_class.parse(url, file_name)
        except ValueError:
            raise MalformedBodyError('invalid value in fileStorageLocation')

        return FileTask(
            remote_file,
            FileMetadata(**object_file),
            message_id,
            object_id,
            file_checksum,
        )

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
                self.destination_bucket,
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
                    '{0}/{0}.metadata'.format(self.object_id),
                )

    def _generate_md5_checksum(self, file_path, buf_size=4096):
        """ Generates a MD5 checksum for inclusion in the upload to s3.
            Uses an iterator over file contents for consistent memory usage.
            """
        md5_checksum = hashlib.md5()
        with open(file_path, 'rb') as f_in:
            for file_chunk in iter(lambda: f_in.read(buf_size), b''):
                md5_checksum.update(file_chunk)
        return base64.b64encode(md5_checksum.digest()).decode('utf-8')

    def upload_bundle(self, destination_bucket, zip_path, metadata, override):
        """ Upload given zip to target

        :param destination_bucket: target s3 bucket
        :type destination_bucket: boto3.S3.Bucket
        :param str zip_path: source file
        :param dict metadata: metadata to set on s3 object
        :param bool override: don't fail if file exists
        :return:
        """
        md5_checksum = self._generate_md5_checksum(zip_path)
        metadata['md5chksum'] = md5_checksum

        if not override:
            if list(destination_bucket.objects.filter(Prefix=self.bundle_name)):
                # TODO: clarify exception
                raise ResourceAlreadyExistsError('object already exists is s3')

        with open(zip_path, 'rb') as data:
            destination_bucket.put_object(
                Body=data,
                Key=self.bundle_name,
                ContentMD5=md5_checksum,
                Metadata=metadata,
            )

    @property
    def bundle_name(self):
        return self.message_id

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
            'bucket': self.destination_bucket.name,
            'status': 'ready',
            'name': '{}.zip'.format(self.bundle_name),
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
