import importlib
import importlib.util
import logging
import logging.config
import os
import re

import yaml

from .remote_urls import S3RemoteUrl


def get_config_path(file_name):
    return os.path.join(
        os.path.abspath(os.path.dirname(__file__)),
        os.pardir,
        'config',
        file_name,
    )


class ConfigError(Exception):
    """ General config related error """

    def __init__(self, message):
        self.msg = message


class ConfigValidationError(ConfigError):
    """ Config validation error """

    def __init__(self, field, message):
        """
        :param str field: config field affected
        :param str message: reason
        """
        super().__init__(message)
        self.field = field


REGIONS = (
    'ap-northeast-1',
    'ap-northeast-2',
    'ap-south-1',
    'ap-southeast-1',
    'ap-southeast-2',
    'ca-central-1',
    'eu-central-1',
    'eu-west-1',
    'eu-west-2',
    'sa-east-1',
    'us-east-1',
    'us-east-2',
    'us-west-1',
    'us-west-2',
)


class Config:
    """
    Configuration object, takes part of settings
    """

    def __init__(
        self,
        environment,
        preservica_base_url,
        input_stream_name,
        invalid_stream_name,
        error_stream_name,
        adaptor_aws_region,
        organisation_buckets,
    ):
        """
        :param str environment: name of the environment (dev/uat/prod)
        :param str input_stream_name: kinesis input stream name
        :param str error_stream_name: kinesis error stream name
        :param str adaptor_aws_region: kinesis error stream region
        :param organisation_buckets: mapping of S3 buckets
        :type organisation_buckets: dict of (str => str)
        """
        self.environment = environment
        self.preservica_base_url = preservica_base_url
        self.input_stream_name = self.validate_stream_name(
            'input_stream_name',
            input_stream_name,
        )
        self.invalid_stream_name = self.validate_stream_name(
            'invalid_stream_name',
            invalid_stream_name,
        )
        self.error_stream_name = self.validate_stream_name(
            'error_stream_name',
            error_stream_name,
        )
        self.adaptor_aws_region = self.validate_region(
            'adaptor_aws_region',
            adaptor_aws_region,
        )

        def prepare_bucket_pair(item):
            key, value = item
            try:
                url = S3RemoteUrl.parse(value)
            except ValueError:
                raise ConfigValidationError(
                    'organisation_buckets',
                    'bucket for {} is not valid s3 url'.format(key),
                )
            return str(key).strip(), url

        self.organisation_buckets = dict(
            map(prepare_bucket_pair, organisation_buckets.items()),
        )

    @staticmethod
    def validate_region(field, value):
        """ Make sure region is from whitelist

        :param str field: field name
        :param str value: raw region value
        :raise: ConfigValidationError if invalid
        :return: region
        """
        if value not in REGIONS:
            raise ConfigValidationError(
                field,
                '{} not valid region'.format(value),
            )
        return value

    @staticmethod
    def validate_stream_name(field, value):
        """ Make sure stream name is valid

        :param str field: field name
        :param str value: raw name value
        :raise: ConfigValidationError if invalid
        :return: name
        """
        if not value or not re.match(r'[a-zA-Z0-9]+', value):
            raise ConfigValidationError(
                field,
                'stream name should match [a-zA-Z0-9]+',
            )
        return value

    @classmethod
    def build(cls, raw):
        """ Build config from python object

        :raise: ConfigError if fails validation
        :param raw:
        """
        return cls(
            raw.environment,
            raw.preservica_base_url,
            raw.input_stream_name,
            raw.invalid_stream_name,
            raw.error_stream_name,
            raw.adaptor_aws_region,
            raw.organisation_buckets,
        )


def load_config(env_name):
    """ Load config for given environment name.

    :param str env_name: environment name
    :return: python object
    :raise: ConfigError if problems loading
    """
    file_path = get_config_path('{}.py'.format(env_name))
    if not os.path.exists(file_path):
        raise ConfigError('file {} not found'.format(file_path))
    try:
        spec = importlib.util.spec_from_file_location('config', file_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return Config.build(mod)
    except ValueError as e:
        raise ConfigError('invalid python config, {}'.format(e))


def load_logger(env_name, simple=False):
    """ Load and apply logging settings for given environment name.

    :param str env_name: environment name
    :raise: ConfigError if problems loading
    """
    if simple:
        logging.basicConfig(level=logging.DEBUG)
        return
    config_path = get_config_path('logging.{}.yaml'.format(env_name))
    load_logger_from_yaml(config_path)


def load_logger_from_yaml(config_path):
    """ Init logger from given yaml file

    :param str config_path: yaml config path
    :raise: ConfigError if problems loading
    """
    if not os.path.exists(config_path):
        raise ConfigError("can't open file {}".format(config_path))

    try:
        with open(config_path) as f:
            logging.config.dictConfig(yaml.load(f.read()))
    except yaml.YAMLError as e:
        raise ConfigError('failed to load yaml config, {}'.format(e))
    except Exception as e:
        raise ConfigError(
            'unexpected error while loading yaml config, {}'.format(e),
        )
