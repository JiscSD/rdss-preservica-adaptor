import base64
import binascii
import json
import logging

from .errors import (
    MalformedJsonBodyError,
    MalformedHeaderError,
    UnsupportedMessageTypeError
)
from .tasks import SUPPORTED_TASKS

logger = logging.getLogger(__name__)

TYPE_TO_TASKS = {x.TYPE: x for x in SUPPORTED_TASKS}


def decode_record(record):
    """ Decode record to json

    :param record: input message
    :type record: amazon_kclpy.messages.Record
    :rtype: dict
    :raise: preservicaservice.errors.MalformedJsonBodyError
    """
    try:
        value = base64.b64decode(record.data)
        message = json.loads(value)
    except (TypeError, ValueError, binascii.Error):
        raise MalformedJsonBodyError()

    if not isinstance(message, dict):
        raise MalformedJsonBodyError()

    return message


def create_supported_tasks(message, config):
    """ Build task out of raw json message

    :param dict message: raw data
    :param preservicaservice.Config config: job config
    :rtype: list of preservicaservice.tasks.BaseTask
    :raise: preservicaservice.errors.UnsupportedMessageTypeError
    :raise: preservicaservice.errors.MalformedHeaderError
    """
    try:
        message_type = message['messageHeader']['messageType']
    except (NameError, KeyError):
        raise MalformedHeaderError()

    if not isinstance(message_type, str):
        raise MalformedHeaderError()

    message_type = message_type.strip()
    if message_type not in TYPE_TO_TASKS:
        raise UnsupportedMessageTypeError(
            '{} is not supported'.format(message_type),
        )

    return TYPE_TO_TASKS[message_type].build(message, config)


def record_to_task(record, config):
    """ Facade to decode record to task instance if possible

    :param record: input message
    :type record: amazon_kclpy.messages.Record
    :param preservicaservice.Config config: job config
    :raise: preservicaservice.errors.MalformedJsonBodyError
    :raise: preservicaservice.errors.UnsupportedMessageTypeError
    :raise: preservicaservice.errors.MalformedHeaderError
    :rtype: preservicaservice.tasks.BaseTask
    """
    message = decode_record(record)
    logger.debug('received message %s', message)
    try:
        return create_supported_tasks(message, config)
    except ValueError as e:
        raise MalformedJsonBodyError(str(e))
