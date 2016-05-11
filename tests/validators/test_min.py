import pytest

from cornflake.exceptions import ValidationError
from cornflake.validators import min_


def test_valid():
    value = min_(1)(2)
    assert value == 2


def test_less_than():
    with pytest.raises(ValidationError):
        min_(10)(9)


def test_equal():
    min_(10)(10)


def test_greater_than():
    min_(10)(11)


def test_units():
    with pytest.raises(ValidationError) as e:
        min_(10, 'kg')(9)

    assert e.value.errors[0] == 'Must be greater than or equal to 10 kg.'
