import json
import logging
import time

import boto3

from .errors import (
    MaxConnectionTriesError,
    MaxMessageSendTriesError,
    ResourceNotFoundError,
    SDKLibraryError
)

logger = logging.getLogger(__name__)


class PutStream:
    """
    Wrapper over kinesis stream to put data.

    Tries to put data several times before gives up.

    Fails on write after N tries, can raise error on creation.
    """

    def __init__(self, stream_name, region, shard_count=1,
                 number_of_tries=10):
        self.stream_name = stream_name
        self.shard_count = shard_count
        self.number_of_tries = number_of_tries
        self.conn = boto3.Session().client('kinesis', region)
        self._init()

    def _init(self):
        """ Verify stream is ready for use or raise error

        :raise: preservicaservice.errors.SDKLibraryError if failed to get
            stream state
        :raise: preservicaservice.errors.ResourceNotFoundError
            if stream deleted
        :raise: preservicaservice.errors.MaxConnectionTriesError if number
            of tries reached
        """
        try:
            status = self._get_stream_status()
        except Exception as e:
            if 'ResourceNotFoundException' in str(e):
                message = 'stream {} not found, {}'.format(
                    self.stream_name, e
                )
                raise ResourceNotFoundError(message)

            message = 'can not connect to stream {}, {}'.format(
                self.stream_name, e
            )
            raise SDKLibraryError(message)

        if 'DELETING' == status:
            message = ('The stream: {} is being deleted, can not proceed'
                       .format(self.stream_name))
            raise ResourceNotFoundError(message)
        elif 'ACTIVE' != status:
            self._wait_for_stream()

    def _get_stream_status(self):
        r = self.conn.describe_stream(StreamName=self.stream_name)
        description = r.get('StreamDescription')
        return description.get('StreamStatus')

    def _wait_for_stream(self):
        """ Wait for the provided stream to become active. """
        status = self._get_stream_status()
        sleep_time_gen = self.wait_generator(
            'stream {} not active after {} tries'.format(
                self.stream_name,
                self.number_of_tries
            ),
            MaxConnectionTriesError
        )
        while status != 'ACTIVE':
            interval = next(sleep_time_gen)
            logger.debug(
                '{} has status: {}, sleeping for {} seconds'.format(
                    self.stream_name,
                    status,
                    self.number_of_tries
                )
            )
            time.sleep(interval)
            status = self._get_stream_status()

    def put(self, data, partition_key='message'):
        """ Put message in stream or fail silently

        :param Any data: object to serialise
        :param string partition_key: partition to use
        """
        try:
            self.put_or_fail(data, partition_key)
        except Exception:
            logger.exception('failed to write data to stream, continue')

    def put_or_fail(self, data, partition_key='message'):
        """ Put message in stream or raise error

        :param Any data: object to serialise
        :param string partition_key: partition to use
        :raise: preservicaservice.errors.MaxMessageSendTriesError if number
            of tries reached
        """
        sleep_time_gen = self.wait_generator(
            'gave up writing data to stream {} after {} tries'.format(
                self.stream_name,
                self.number_of_tries
            ),
            MaxMessageSendTriesError
        )
        for interval in sleep_time_gen:
            try:
                if isinstance(data, (dict, list, tuple)):
                    data = json.dumps(data)
                if isinstance(data, bytes):
                    data = bytes(data)
                self.conn.put_record(
                    StreamName=self.stream_name,
                    Data=data,
                    PartitionKey=partition_key
                )
                break
            except Exception:
                logger.debug(
                    'failed to write {}, sleeping for {} seconds'.format(
                        self.stream_name,
                        interval
                    )
                )
                time.sleep(interval)

    def wait_generator(self, message, error):
        return exponential_generator(
            message,
            error,
            count=self.number_of_tries,
            multiplier=0.1
        )


def exponential_generator(message, error, count=10, step=1, multiplier=100.0):
    """ Produce exponential values """
    i = 1
    while i <= count:
        value = pow(2, i) * multiplier
        yield value
        i += step

    raise error(message)
