import pytest

from preservicaservice.config import Config
from tests.helpers import named_temp_file


@pytest.fixture
def temp_file():
    for i in named_temp_file():
        yield i


@pytest.fixture
def temp_file2():
    for i in named_temp_file():
        yield i


@pytest.fixture
def temp_file3():
    for i in named_temp_file():
        yield i


@pytest.fixture
def valid_config():
    return Config(
        'input',
        'eu-west-1',
        'error',
        'eu-west-1',
        organisation_buckets={'1': 's3://upload/to'},
    )
