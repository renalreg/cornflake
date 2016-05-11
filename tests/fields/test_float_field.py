from decimal import Decimal

import pytest

from cornflake.fields import FloatField, ValidationError


@pytest.mark.parametrize(('value', 'expected'), [
    (123, 123),
    (123.456, 123.456),
    (Decimal(123.456), 123.456),
])
def test_to_representation(value, expected):
    assert FloatField().to_representation(value) == expected


@pytest.mark.parametrize(('data', 'expected'), [
    (123.456, 123.456),
    (-123.456, -123.456),
    ('123.456', 123.456),
    ('+123.456', 123.456),
    ('-123.456', -123.456),
    (' 123.456 ', 123.456),  # whitespace
    (123, 123),
    (Decimal('123.456'), 123.456),
    (True, 1),
    (False, 0)
])
def test_to_internal_value(data, expected):
    assert FloatField().to_internal_value(data) == expected


@pytest.mark.parametrize('data', [
    'hello',
    {'foo': 1, 'bar': 2},
    ['foo', 'bar', 'baz'],
])
def test_to_internal_value_invalid(data):
    with pytest.raises(ValidationError):
        FloatField().to_internal_value(data)
