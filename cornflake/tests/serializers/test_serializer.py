from datetime import date

import pytest

from cornflake.serializers import Serializer
from cornflake import fields
from cornflake.exceptions import ValidationError, SkipField


def test_fields():
    class TagField(fields.Field):
        def __init__(self, tag, **kwargs):
            super(TagField, self).__init__(**kwargs)
            self.tag = tag

    class FooSerializer(Serializer):
        foo = TagField('foo_foo')
        bar = TagField('foo_bar')
        baz = TagField('foo_baz')

    class BarSerializer(Serializer):
        hello = TagField('bar_hello')
        bar = TagField('bar_bar')

    class QuxMixin(object):
        qux = TagField('qux_qux')
        norf = TagField('qux_norf')

    class XMixin(object):
        x = TagField('x_x')
        y = TagField('x_y')
        z = TagField('x_z')
        norf = TagField('x_norf')

    class YMixin(object):
        y = TagField('y_y')
        z = TagField('y_z')
        norf = TagField('y_norf')

    class NorfMixin(YMixin, XMixin):
        norf = TagField('norf_norf')

    class BazSerializer(NorfMixin, BarSerializer, QuxMixin, FooSerializer):
        baz = TagField('baz_baz')
        world = TagField('baz_world')

    serializer = BazSerializer()

    expected = [
        ('foo', 'foo_foo'),
        ('qux', 'qux_qux'),
        ('hello', 'bar_hello'),
        ('bar', 'bar_bar'),
        ('x', 'x_x'),
        ('y', 'y_y'),
        ('z', 'y_z'),
        ('norf', 'norf_norf'),
        ('baz', 'baz_baz'),
        ('world', 'baz_world'),
    ]

    serializer_fields = serializer.fields

    assert serializer_fields.keys() == [x[0] for x in expected]
    assert [(x.field_name, x.tag) for x in serializer_fields.values()] == expected

    for name, tag in expected:
        field = getattr(serializer, name)
        assert field.tag == tag
        assert field.field_name == name


def test_validate_error():
    class FooSerializer(Serializer):
        def __init__(self, message):
            super(FooSerializer, self).__init__()
            self.message = message

        def validate(self, data):
            raise ValidationError(self.message)

    serializer = FooSerializer('Uh oh!')

    with pytest.raises(ValidationError) as e:
        serializer.run_validation({})

    assert e.value.errors == {
        '_': ['Uh oh!']
    }

    serializer = FooSerializer({'_': 'Uh oh!'})

    with pytest.raises(ValidationError) as e:
        serializer.run_validation({})

    assert e.value.errors == {
        '_': ['Uh oh!']
    }


def test_validate_field_error():
    class FooSerializer(Serializer):
        foo = fields.StringField()

        def validate_foo(self, foo):
            raise ValidationError('Uh oh!')

    serializer = FooSerializer()

    with pytest.raises(ValidationError) as e:
        serializer.run_validation({'foo': 'bar'})

    assert e.value.errors == {
        'foo': ['Uh oh!']
    }


def test_field_error():
    class FooSerializer(Serializer):
        foo = fields.IntegerField()

    serializer = FooSerializer()

    with pytest.raises(ValidationError) as e:
        serializer.run_validation({'foo': 'bar'})

    assert e.value.errors == {
        'foo': ['A valid integer is required.']
    }


def test_is_valid():
    class FooSerializer(Serializer):
        foo = fields.IntegerField()

    serializer = FooSerializer(data={'foo': 1})

    assert serializer.is_valid()

    serializer = FooSerializer(data={'foo': 'bar'})

    assert not serializer.is_valid()

    assert serializer.errors == {
        'foo': ['A valid integer is required.']
    }

    with pytest.raises(ValidationError) as e:
        serializer.is_valid(raise_exception=True)

    assert e.value.errors == {
        'foo': ['A valid integer is required.']
    }


def test_to_representation():
    class FooSerializer(Serializer):
        foo = fields.DateField()

    serializer = FooSerializer({'foo': date(2001, 2, 3)})

    assert serializer.data == {'foo': '2001-02-03'}


def test_to_representation_skip():
    class FooField(fields.Field):
        def get_attribute(self, instance):
            raise SkipField

    class FooSerializer(Serializer):
        foo = FooField()

    serializer = FooSerializer({'foo': 'bar'})

    assert serializer.data == {}


def test_to_representation_none():
    class FooField(fields.Field):
        def to_representation(self, value):
            return 'fail!'

    class FooSerializer(Serializer):
        foo = FooField()

    serializer = FooSerializer({'foo': None})

    assert serializer.data == {'foo': None}


def test_context():
    class FooField(fields.Field):
        def to_representation(self, value):
            return self.context['message']

    class FooSerializer(Serializer):
        foo = FooField()

    class BarSerializer(Serializer):
        foo = FooSerializer()

    serializer = BarSerializer({'foo': {'foo': 'bar'}}, context={'message': 'Hello!'})

    assert serializer.data == {
        'foo': {'foo': 'Hello!'}
    }


@pytest.mark.parametrize(('data', 'expected'), [
    ({'foo': 1}, {'foo': 1}),
    ({'foo': '1'}, {'foo': 1}),
    ({'foo': 1, 'bar': 1}, {'foo': 1}),  # removes extra values
])
def test_to_internal_value(data, expected):
    class FooSerializer(Serializer):
        foo = fields.IntegerField()

    serializer = FooSerializer(data=data)
    assert serializer.is_valid()
    assert serializer.validated_data == expected
    assert serializer.to_internal_value(data) == expected


@pytest.mark.parametrize('data', [
    {},
    [],
    True,
    False,
    123,
    123.456
])
def test_to_internal_value_invalid(data):
    class FooSerializer(Serializer):
        foo = fields.IntegerField()

    serializer = FooSerializer(data=data)
    assert not serializer.is_valid()
    assert serializer.errors
    assert serializer.validated_data == {}

    with pytest.raises(ValidationError):
        serializer.to_internal_value(data)


def test_data():
    class FooSerializer(Serializer):
        foo = fields.DateField()

    data = {'foo': '2001-02-03'}
    instance = {'foo': date(2001, 02, 03)}

    serializer = FooSerializer(instance)
    assert serializer.data == data

    serializer = FooSerializer(data=data)
    assert serializer.is_valid()
    assert serializer.validated_data == instance
    assert serializer.initial_data == data
    assert serializer.data == data

    serializer = FooSerializer(data={'foo': 'hello'})
    assert not serializer.is_valid()
    assert serializer.data == {}

    serializer = FooSerializer(instance, data={'foo': 'hello'})
    assert not serializer.is_valid()
    assert serializer.data == data
