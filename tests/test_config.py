import pytest

from preservicaservice import config


@pytest.mark.parametrize(
    'env', [
        'dev',
        'uat',
        'prod',
        'test',
    ],
)
def test_load_conf(env):
    conf = config.load_config(env)
    assert isinstance(conf, config.Config)


def test_load_conf_missing():
    with pytest.raises(config.ConfigError, match='xxx.py not found'):
        config.load_config('xxx')


@pytest.mark.parametrize(
    'env', [
        'dev',
        'uat',
        'prod',
        'test',
    ],
)
def test_load_logger(env):
    config.load_logger(env)


def test_load_logger_missing():
    with pytest.raises(config.ConfigError, match="can't open file .*"):
        config.load_logger('xxx')


def test_load_logger_from_yaml_non_yaml(temp_file):
    with open(temp_file, 'w') as f:
        f.write('abc')

    with pytest.raises(
        config.ConfigError,
        match='unexpected error while loading yaml',
    ):
        config.load_logger_from_yaml(temp_file)


@pytest.fixture
def valid_config_arguments():
    return dict(
        environment='test',
        preservica_base_url='https://test_preservica_url',
        input_stream_name='in',
        input_stream_region='eu-west-2',
        invalid_stream_name='invalid',
        invalid_stream_region='eu-west-2',
        error_stream_name='err',
        error_stream_region='eu-west-2',
        organisation_buckets={
            '1': 's3://upload/to/1',
            '2': 's3://upload/to/2',
        },
    )


def test_valid_config(valid_config_arguments):
    arguments = valid_config_arguments
    c = config.Config(**arguments)
    assert c.input_stream_name == arguments['input_stream_name']
    assert c.input_stream_region == arguments['input_stream_region']
    assert c.error_stream_name == arguments['error_stream_name']
    assert c.error_stream_region == arguments['error_stream_region']
    assert len(c.organisation_buckets) == 2
    assert c.organisation_buckets['1'].url == arguments['organisation_buckets']['1']
    assert c.organisation_buckets['2'].url == arguments['organisation_buckets']['2']


@pytest.mark.parametrize(
    'arguments,error', [
        (
            dict(organisation_buckets={
                'x': 'http://upload/to',
            }), 'organisation_buckets',
        ),
        (dict(input_stream_name=' '), 'input_stream_name'),
        (dict(input_stream_name='ßßß'), 'input_stream_name'),
        (dict(input_stream_region='eu-north-2'), 'input_stream_region'),
        (dict(error_stream_name='-3'), 'error_stream_name'),
        (dict(error_stream_region='eu-1'), 'error_stream_region'),
    ],
)
def test_config_validation(valid_config_arguments, arguments, error):
    valid_config_arguments.update(arguments)
    with pytest.raises(config.ConfigValidationError, match=error):
        config.Config(**valid_config_arguments)
