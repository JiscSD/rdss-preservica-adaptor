import pytest

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
