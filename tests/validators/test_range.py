import pytest

from cornflake.exceptions import ValidationError
from cornflake.validators import range_


def test_valid():
    value = range_(min_value=3, max_value=5)(4)
    assert value == 4


def test_min_less_than():
    with pytest.raises(ValidationError):
        range_(min_value=10)(9)


def test_min_equal():
    range_(min_value=10)(10)


def test_min_greater_than():
    range_(min_value=10)(11)


def test_max_less_than():
    range_(max_value=10)(9)


def test_max_equal():
    range_(max_value=10)(10)


def test_max_greater_than():
    with pytest.raises(ValidationError):
        range_(max_value=10)(11)


def test_min_max_less_than():
    with pytest.raises(ValidationError):
        range_(10, 20)(5)


def test_min_max_equal_min():
    range_(10, 20)(10)


def test_min_max_middle():
    range_(10, 20)(15)


def test_min_max_equal_max():
    range_(10, 20)(20)


def test_min_max_greater_than():
    with pytest.raises(ValidationError):
        range_(10, 20)(21)
