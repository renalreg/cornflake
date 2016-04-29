import pytest

from cornflake.fields import IntegerField, ValidationError


@pytest.mark.parametrize(('value', 'expected'), [
    (-123, -123),
    (0, 0),
    (123, 123),
])
def test_to_representation(value, expected):
    assert IntegerField().to_representation(value) == expected


@pytest.mark.parametrize(('data', 'expected'), [
    ('123', 123),
    ('+123', 123),
    ('-123', -123),
    ('0100', 100),
    (' 123 ', 123),  # whitespace
    (123, 123),
    (-123, -123),
    (True, 1),
    (False, 0),
])
def test_to_internal_value(data, expected):
    assert IntegerField().to_internal_value(data) == expected


@pytest.mark.parametrize('data', [
    123.456,
    '123.456',
    'hello',
    '',
    {'foo': 1, 'bar': 2},
    ['foo', 'bar', 'baz'],
])
def test_to_internal_value_invalid(data):
    with pytest.raises(ValidationError):
        IntegerField().to_internal_value(data)
