import copy

import pytest

from cornflake.fields import Field, empty
from cornflake.exceptions import ValidationError, SkipField


class BasicField(Field):
    def to_internal_value(self, data):
        return data

    def to_representation(self, value):
        return value


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


def test_get_value():
    field = Field()
    field.bind(None, 'a')
    assert field.get_value({'a': 'b'}) == 'b'
    assert field.get_value({}) is empty


def test_get_attribute():
    class o:
        a = 'b'

    d = {'a': 'b'}

    field = Field()
    field.bind(None, 'a')

    assert field.get_attribute(o) == 'b'
    assert field.get_attribute(d) == 'b'

    field = Field()
    field.bind(None, 'b')

    with pytest.raises(AttributeError):
        field.get_attribute(o)

    with pytest.raises(KeyError):
        field.get_attribute(d)

    field.required = False

    with pytest.raises(SkipField):
        field.get_attribute(o)

    with pytest.raises(SkipField):
        field.get_attribute(d)


def test_default():
    field = BasicField(default='foo')
    assert field.run_validation('bar') == 'bar'
    assert field.run_validation(None) is None
    assert field.run_validation(empty) == 'foo'


def test_default_callable():
    def f():
        f.counter += 1
        return f.counter

    f.counter = 0

    field = BasicField(default=f)

    assert field.run_validation('bar') == 'bar'
    assert field.run_validation(None) is None
    assert field.run_validation(empty) == 1
    assert field.run_validation(empty) == 2


def test_required():
    field = BasicField(required=True)

    assert field.run_validation(123) == 123

    with pytest.raises(ValidationError):
        field.run_validation(None)

    with pytest.raises(ValidationError):
        field.run_validation(empty)


def test_optional():
    field = BasicField(required=False)

    assert field.run_validation(123) == 123
    assert field.run_validation(None) is None
    assert field.run_validation(empty) is None


def test_null():
    field = BasicField(null=True)
    assert field.run_validation(None) is None

    field = BasicField(null=False)

    with pytest.raises(ValidationError):
        field.run_validation(None)


def test_to_representation():
    field = Field()

    with pytest.raises(NotImplementedError):
        field.to_representation(123)


def test_to_internal_value():
    field = Field()

    with pytest.raises(NotImplementedError):
        field.to_internal_value(123)


def test_validators():
    field = BasicField(validators=[lambda x: 2 * x, lambda x: x + 1])
    assert field.run_validation(2) == 5


def test_validators_error():
    def error(value):
        raise ValidationError('Uh oh!')

    field = BasicField(validators=[error])

    with pytest.raises(ValidationError):
        field.run_validation(123)


def test_validators_skip():
    def skip(value):
        raise SkipField

    field = BasicField(validators=[lambda x: x + 1, skip])

    assert field.run_validation(1) == 2


def test_set_context():
    class f():
        def __init__(self):
            self.parent = None

        def __call__(self, value):
            return self.parent.foo

        def set_context(self, parent):
            self.parent = parent

    field = BasicField(validators=[f()])
    field.foo = 'bar'

    assert field.run_validation(123) == 'bar'
