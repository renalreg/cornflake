import pytest

from cornflake.exceptions import ValidationError
from cornflake.validators import required


def test_str():
    value = required()('hello')
    assert value == 'hello'


def test_int():
    value = required()(123)
    assert value == 123


def test_empty():
    value = required()('')
    assert value == ''


def test_none():
    with pytest.raises(ValidationError):
        required()(None)
