import pytest
from enum import Enum

from cornflake.fields import EnumField, ValidationError


class Foo(Enum):
    a = 'foo'
    b = 'bar'


@pytest.mark.parametrize(('value', 'expected'), [
    (Foo.a, 'foo'),
    ('foo', 'foo'),
])
def test_to_representation(value, expected):
    assert EnumField(Foo).to_representation(value) == expected


@pytest.mark.parametrize(('data', 'expected'), [
    ('foo', Foo.a),
    ('bar', Foo.b),
    (Foo.a, Foo.a),
    (Foo.b, Foo.b),
])
def test_to_internal_value(data, expected):
    assert EnumField(Foo).to_internal_value(data) == expected


@pytest.mark.parametrize('data', [
    'c',
    123,
    123.456,
    True,
    False,
    {'foo': 1, 'bar': 2},
    ['foo', 'bar', 'baz'],
])
def test_to_internal_value_invalid(data):
    with pytest.raises(ValidationError):
        EnumField(Foo).to_internal_value(data)
