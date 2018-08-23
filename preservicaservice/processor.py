import logging

from amazon_kclpy import kcl

from .errors import (
    BaseError,
    ExpiredMessageError,
    MalformedBodyError,
    MalformedHeaderError,
    UnknownErrorError,
    UnsupportedMessageTypeError,
    InvalidChecksumError,
)
from .put_stream import PutStream
from .tasks_parser import record_to_task

logger = logging.getLogger(__name__)


class RecordProcessor(kcl.RecordProcessorBase):
    """ Records processor which can report failures to specific
    kinesis stream.
    """

    def __init__(self, config):
        """
        :param config: job config object
        :type config: preservicaservice.config.Config
        """
        self.config = config
        self.invalid_stream = PutStream(
            config.invalid_stream_name,
            config.invalid_stream_region,
        )
        self.error_stream = PutStream(
            config.error_stream_name,
            config.error_stream_region,
        )

    def initialize(self, shard_id):
        pass

    def process_records(self, records, checkpointer):
        """ Handle list of records

        :param records: input records
        :param checkpointer: checkpoint object
        :return:
        """
        logger.debug('received %d records', len(records))
        for i, record in enumerate(records):
            self.process_record(i, record)
        logger.debug('complete')

    def shutdown_requested(self, checkpointer):
        pass

    def shutdown(self, checkpointer, reason):
        pass

    def process_record(self, index, record):
        """ Handle single record.

        Make sure it never fails.

        :param int index: which item in given batch it is
        :param Record record: data to handle
        """
        try:
            logger.debug('processing record %d', index)
            task = record_to_task(record, self.config)
            if task:
                task.run()
            else:
                logger.warning('no task out of message')
        except (MalformedBodyError, UnsupportedMessageTypeError, ExpiredMessageError, MalformedHeaderError, InvalidChecksumError) as e:
            print('invalid')
            logger.exception('invalid message')
            self.invalid_stream.put(e.export(record))
        except BaseError as e:
            print('error')
            logger.exception('error handling record')
            self.error_stream.put(e.export(record))
        except Exception as e:
            print('unknown')
            logger.exception('unexpected error handling error')
            self.error_stream.put(UnknownErrorError(str(e)).export(record))
