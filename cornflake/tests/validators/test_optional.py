import pytest

from cornflake.exceptions import SkipField
from cornflake.validators import optional


def test_str():
    value = optional()('hello')
    assert value == 'hello'


def test_none():
    with pytest.raises(SkipField):
        optional()(None)


def test_empty():
    value = optional()('')
    assert value == ''
