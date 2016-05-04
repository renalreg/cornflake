import pytest

from cornflake.fields import StringField, ValidationError


@pytest.mark.parametrize(('value', 'expected'), [
    ('hello', 'hello'),
    (u'\u263A', u'\u263A'),
])
def test_to_representation(value, expected):
    assert StringField().to_representation(value) == expected


@pytest.mark.parametrize(('data', 'expected'), [
    ('hello', 'hello'),
    (u'\u263A', u'\u263A'),  # unicode
    (123, '123'),
    (123.456, '123.456'),
    (' foo ', 'foo'),  # strip whitespace
])
def test_to_internal_value(data, expected):
    assert StringField().to_internal_value(data) == expected


@pytest.mark.parametrize('data', [
    True,
    False,
    {'foo': 1, 'bar': 2},
    ['foo', 'bar', 'baz'],
])
def test_to_internal_value_invalid(data):
    with pytest.raises(ValidationError):
        StringField().to_internal_value(data)


def test_trim_whitespace_true():
    field = StringField(trim_whitespace=True)
    value = field.to_internal_value(' abc ')
    assert value == 'abc'


def test_trim_whitespace_false():
    field = StringField(trim_whitespace=False)
    value = field.to_internal_value(' abc ')
    assert value == ' abc '
