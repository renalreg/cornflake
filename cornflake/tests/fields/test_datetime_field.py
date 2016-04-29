from datetime import date, datetime

import pytest
import pytz

from cornflake.fields import DateTimeField, ValidationError


@pytest.mark.parametrize(('value', 'expected'), [
    (datetime(2001, 2, 3, 12, 34, 56), '2001-02-03T12:34:56'),
    (datetime(999, 2, 3, 12, 34, 56), '0999-02-03T12:34:56'),
    (datetime(2001, 2, 3, 12, 34, 56, tzinfo=pytz.utc), '2001-02-03T12:34:56+00:00'),
])
def test_to_representation(value, expected):
    assert DateTimeField().to_representation(value) == expected


@pytest.mark.parametrize(('data', 'expected'), [
    ('2001-02-03 12:34:56', datetime(2001, 2, 3, 12, 34, 56, tzinfo=pytz.utc)),
    ('2001-02-03T12:34:56', datetime(2001, 2, 3, 12, 34, 56, tzinfo=pytz.utc)),
    ('2001-02-03T12:34:56-01:00', datetime(2001, 2, 3, 13, 34, 56, tzinfo=pytz.utc)),
    ('2001-02-03T12:34:56+01:00', datetime(2001, 2, 3, 11, 34, 56, tzinfo=pytz.utc)),
    ('2001-02-03', datetime(2001, 2, 3, 0, 0, 0, tzinfo=pytz.utc)),
    (datetime(2001, 2, 3, 12, 34, 56), datetime(2001, 2, 3, 12, 34, 56)),
])
def test_to_internal_value(data, expected):
    assert DateTimeField().to_internal_value(data) == expected


@pytest.mark.parametrize('data', [
    '2001-13-03T12:34:56',
    '2001-02-29T12:34:56',
    '2001-02-03T24:34:56',
    '2001-02-03T12:60:56',
    '2001-02-03T12:34:60',
    date(2001, 2, 3),
    2000,
    2000.1,
    True,
    False,
    'hello',
    {'foo': 1, 'bar': 2},
    ['foo', 'bar', 'baz'],
])
def test_to_internal_value_invalid(data):
    with pytest.raises(ValidationError):
        DateTimeField().to_internal_value(data)
