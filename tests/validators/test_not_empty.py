import pytest

from cornflake.exceptions import ValidationError
from cornflake.validators import not_empty


def test_str():
    value = not_empty()('hello')
    assert value == 'hello'


def test_list():
    value = not_empty()(['hello', 'world'])
    assert value == ['hello', 'world']


def test_empty_str():
    with pytest.raises(ValidationError):
        not_empty()('')


def test_empty_list():
    with pytest.raises(ValidationError):
        not_empty()([])


def test_none():
    with pytest.raises(ValidationError):
        not_empty()(None)
