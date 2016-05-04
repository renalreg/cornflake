import copy

from cornflake.fields import Field


def test_root():
    class Node(object):
        def __init__(self, parent=None):
            self.parent = parent

    context = object()

    root = Node()
    root._context = context

    level1 = Node(root)
    level2 = Node(level1)

    field = Field()
    field.bind(level2)

    assert field.root is root
    assert field.context is context


def test_error_messages():
    class Foo(Field):
        error_messages = {
            'a': 'b',
            'c': 'd',
        }

    field = Foo()
    assert field.error_messages['a'] == 'b'

    field = Foo(error_messages={'a': 'e'})
    assert field.error_messages['a'] == 'e'
    assert field.error_messages['c'] == 'd'


def test_source():
    class o:
        a = 'b'
        c = 'd'

    d = {
        'a': 'b',
        'c': 'd',
    }

    field = Field()
    field.bind(None, 'a')
    assert field.get_attribute(o) == 'b'
    assert field.get_attribute(d) == 'b'
    assert field.get_value(d) == 'b'

    field = Field(source='c')
    field.bind(None, 'a')
    assert field.get_attribute(o) == 'd'
    assert field.get_attribute(d) == 'd'
    assert field.get_value(d) == 'b'


def test_deepcopy():
    field = Field(source='foo')
    field.foo = 'bar'
    field = copy.deepcopy(field)
    assert field.source == 'foo'
    assert not hasattr(field, 'foo')
