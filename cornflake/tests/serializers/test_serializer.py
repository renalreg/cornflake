from cornflake.serializers import Serializer
from cornflake.fields import Field


class TagField(Field):
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


def test_fields():
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

    fields = serializer.fields

    assert fields.keys() == [x[0] for x in expected]
    assert [(x.field_name, x.tag) for x in fields.values()] == expected

    for name, tag in expected:
        field = getattr(serializer, name)
        assert field.tag == tag
        assert field.field_name == name
