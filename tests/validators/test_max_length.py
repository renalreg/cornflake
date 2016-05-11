import pytest

from cornflake.exceptions import ValidationError
from cornflake.validators import max_length


def test_valid():
    value = max_length(3)('abc')
    assert value == 'abc'


def test_empty():
    max_length(3)('')


def test_shorter():
    max_length(3)('aa')


def test_equal():
    max_length(3)('aaa')


def test_longer():
    with pytest.raises(ValidationError):
        max_length(3)('aaaa')
