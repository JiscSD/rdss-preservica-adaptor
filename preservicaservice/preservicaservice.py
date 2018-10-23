#!/usr/bin/env python
import logging
import os
import sys

from amazon_kclpy import kcl

from .config import load_logger, load_config
from .processor import RecordProcessor

logger = logging.getLogger(__name__)


def main():
    """ Entry point.

    Makes sure
    - config loaded
    - logger set
    - processor created
    - processing loop started

    Does exit if required and sends log to stderr on early failure.

    """
    env = os.environ.get('ENVIRONMENT')
    if not env:
        sys.stderr.write('env variable ENVIRONMENT is not set')
        sys.exit(2)

    try:
        conf = load_config(env)
    except Exception as e:
        sys.stderr.write(str(e))
        sys.exit(2)

    try:
        load_logger(env)
    except Exception as e:
        sys.stderr.write(str(e))
        sys.exit(2)

    logger.info('loaded config for {}'.format(env))

    try:
        record_processor = RecordProcessor(conf)
    except Exception:
        logger.exception('failed to create processor')
        sys.exit(2)

    process = kcl.KCLProcess(record_processor)
    process.run()


if __name__ == '__main__':
    main()
