from datetime import date

import pytest

from cornflake.fields import ListField, DateField, StringField, IntegerField
from cornflake.serializers import Serializer
from cornflake.exceptions import ValidationError


@pytest.mark.parametrize(('value', 'expected'), [
    ([], []),
    ([date(2016, 1, 1), date(2016, 1, 2)], ['2016-01-01', '2016-01-02']),
    ([date(2016, 1, 1), None, date(2016, 1, 2)], ['2016-01-01', None, '2016-01-02']),
])
def test_to_representation(value, expected):
    assert ListField(child=DateField()).to_representation(value) == expected


@pytest.mark.parametrize(('data', 'expected'), [
    ([], []),
    (['2016-01-01', '2016-01-02'], [date(2016, 1, 1), date(2016, 1, 2)]),
    ([date(2016, 1, 1), date(2016, 1, 2)], [date(2016, 1, 1), date(2016, 1, 2)]),
])
def test_to_internal_value(data, expected):
    assert ListField(child=DateField()).to_internal_value(data) == expected


@pytest.mark.parametrize('data', [
    '2016-01-01,2016-01-02',
    123,
    123.456,
    True,
    False,
    {'foo': 1, 'bar': 2},
    ['foo', 'bar', 'baz'],
])
def test_to_internal_value_invalid(data):
    with pytest.raises(ValidationError):
        ListField(child=DateField()).to_internal_value(data)


def test_none():
    i = ['2016-01-01', None, '2016-01-02']
    o = [date(2016, 1, 1), None, date(2016, 1, 2)]

    with pytest.raises(ValidationError):
        ListField(child=DateField(null=False)).to_internal_value(i)

    assert ListField(child=DateField(null=True)).to_internal_value(i) == o


def test_string_field():
    field = ListField(child=StringField())

    assert field.to_internal_value(['foo', 'bar']) == ['foo', 'bar']

    with pytest.raises(ValidationError):
        field.to_internal_value('foo')


def test_field_errors():
    field = ListField(child=IntegerField())

    with pytest.raises(ValidationError) as e:
        field.to_internal_value(['123', 'foo'])

    assert e.value.errors == {1: ['A valid integer is required.']}


def test_serializer_errors():
    class FooSerializer(Serializer):
        foo = IntegerField()

    field = ListField(child=FooSerializer())

    with pytest.raises(ValidationError) as e:
        field.to_internal_value([{'foo': '123'}, {'foo': 'foo'}])

    assert e.value.errors == {1: {'foo': ['A valid integer is required.']}}
