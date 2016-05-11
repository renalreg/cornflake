import pytest

from cornflake.exceptions import ValidationError
from cornflake.validators import in_


def test_in_list():
    value = in_([1, 2, 3])(1)
    assert value == 1


def test_not_in_list():
    with pytest.raises(ValidationError):
        in_([1, 2, 3])(4)
