from datetime import date

import pytest

from cornflake.fields import CommaSeparatedField, DateField, ValidationError


@pytest.mark.parametrize(('value', 'expected'), [
    ([date(2016, 1, 1), date(2016, 1, 2)], '2016-01-01,2016-01-02'),
    ([], ''),
])
def test_to_representation(value, expected):
    assert CommaSeparatedField(child=DateField()).to_representation(value) == expected


@pytest.mark.parametrize(('data', 'expected'), [
    ('', []),
    ([], []),
    ('2016-01-01', [date(2016, 1, 1)]),
    ('2016-01-01,2016-01-02', [date(2016, 1, 1), date(2016, 1, 2)]),
    (['2016-01-01', '2016-01-02'], [date(2016, 1, 1), date(2016, 1, 2)]),
    ([date(2016, 1, 1), date(2016, 1, 2)], [date(2016, 1, 1), date(2016, 1, 2)]),
])
def test_to_internal_value(data, expected):
    assert CommaSeparatedField(child=DateField()).to_internal_value(data) == expected


@pytest.mark.parametrize('data', [
    '1,2,3',
    123,
    123.456,
    True,
    False,
    {'foo': 1, 'bar': 2},
    ['foo', 'bar', 'baz'],
])
def test_to_internal_value_invalid(data):
    with pytest.raises(ValidationError):
        CommaSeparatedField(child=DateField()).to_internal_value(data)
