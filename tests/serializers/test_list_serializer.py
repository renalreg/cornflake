from datetime import date

import pytest

from cornflake import fields
from cornflake.serializers import Serializer, ListSerializer
from cornflake.exceptions import ValidationError
from cornflake.fields import empty


class FooSerializer(Serializer):
    foo = fields.DateField()


@pytest.mark.parametrize(('value', 'expected'), [
    ([], []),
    ([{'foo': date(2016, 1, 1)}, {'foo': date(2016, 1, 2)}], [{'foo': '2016-01-01'}, {'foo': '2016-01-02'}]),
    ([{'foo': date(2016, 1, 1)}, None, {'foo': date(2016, 1, 2)}], [{'foo': '2016-01-01'}, None, {'foo': '2016-01-02'}]),
])
def test_to_representation(value, expected):
    serializer = ListSerializer(value, child=FooSerializer())
    assert serializer.data == expected


@pytest.mark.parametrize(('data', 'expected'), [
    ([], []),
    ([{'foo': '2016-01-01'}, {'foo': '2016-01-02'}], [{'foo': date(2016, 1, 1)}, {'foo': date(2016, 1, 2)}]),
    ([{'foo': date(2016, 1, 1)}, {'foo': date(2016, 1, 2)}], [{'foo': date(2016, 1, 1)}, {'foo': date(2016, 1, 2)}]),
])
def test_to_internal_value(data, expected):
    serializer = ListSerializer(child=FooSerializer(), data=data)
    assert serializer.is_valid()
    assert serializer.validated_data == expected


@pytest.mark.parametrize('data', [
    'hello',
    123,
    123.456,
    True,
    False,
    {'foo': 1, 'bar': 2},
    ['foo', 'bar', 'baz'],
])
def test_to_internal_value_invalid(data):
    serializer = ListSerializer(child=FooSerializer(), data=data)
    assert not serializer.is_valid()
    assert serializer.errors


def test_none():
    i = [{'foo': '2016-01-01'}, None, {'foo': '2016-01-02'}]
    o = [{'foo': date(2016, 1, 1)}, None, {'foo': date(2016, 1, 2)}]

    with pytest.raises(ValidationError):
        ListSerializer(child=FooSerializer(required=True)).to_internal_value(i)

    assert ListSerializer(child=FooSerializer(required=False)).to_internal_value(i) == o


def test_error():
    data = [
        {'foo': '2016-01-01'},
        {'foo': 'hello'},
    ]

    serializer = ListSerializer(child=FooSerializer(), data=data)

    assert not serializer.is_valid()

    assert serializer.errors == {
        1: {'foo': ['Invalid date format.']}
    }


def test_validate_error():
    class FooListSerializer(ListSerializer):
        child = FooSerializer()

        def __init__(self, message, **kwargs):
            super(FooListSerializer, self).__init__(**kwargs)
            self.message = message

        def validate(self, data):
            raise ValidationError(self.message)

    serializer = FooListSerializer('Uh oh!', data=[])
    assert not serializer.is_valid()
    assert serializer.errors == {'_': ['Uh oh!']}

    serializer = FooListSerializer({'_': 'Uh oh!'}, data=[])
    assert not serializer.is_valid()
    assert serializer.errors == {'_': ['Uh oh!']}


def test_default():
    field = ListSerializer(required=False, child=fields.IntegerField())

    # Default should be an empty list
    assert field.run_validation(empty) == []
    assert field.run_validation(None) == []
