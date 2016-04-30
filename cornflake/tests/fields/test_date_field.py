from datetime import date, datetime

import pytest

from cornflake.fields import DateField, ValidationError


@pytest.mark.parametrize(('value', 'expected'), [
    (date(2001, 2, 3), '2001-02-03'),
    (date(999, 1, 1), '0999-01-01'),  # dates before 1900 can cause problems
])
def test_to_representation(value, expected):
    assert DateField().to_representation(value) == expected


@pytest.mark.parametrize(('data', 'expected'), [
    ('2001-02-03', date(2001, 2, 3)),
    ('0999-2-3', date(999, 2, 3)),
    ('2001-02-03T12:34:56', date(2001, 2, 3)),
    ('2001-02-03 12:34:56', date(2001, 2, 3)),
])
def test_to_internal_value(data, expected):
    assert DateField().to_internal_value(data) == expected


@pytest.mark.parametrize('data', [
    '2001-02-29',
    '2001-13-03',
    datetime(2001, 2, 3, 12, 34, 56),
    123,
    123.456,
    True,
    False,
    {'foo': 1, 'bar': 2},
    ['foo', 'bar', 'baz'],
])
def test_to_internal_value_invalid(data):
    with pytest.raises(ValidationError):
        DateField().to_internal_value(data)
