import pytest

from cornflake.exceptions import ValidationError
from cornflake.validators import max_


def test_valid():
    value = max_(10)(5)
    assert value == 5


def test_less_than():
    max_(10)(9)


def test_equal():
    max_(10)(10)


def test_greater_than():
    with pytest.raises(ValidationError):
        max_(10)(11)


def test_units():
    with pytest.raises(ValidationError) as e:
        max_(10, 'kg')(11)

    assert e.value.errors[0] == 'Must be less than or equal to 10 kg.'
