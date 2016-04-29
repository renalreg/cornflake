import pytest

from cornflake.fields import BooleanField, ValidationError


@pytest.mark.parametrize(('value', 'expected'), [
    (True, True),
    (False, False),
    (1, True),
    (0, False),
])
def test_to_representation(value, expected):
    assert BooleanField().to_representation(value) is expected


@pytest.mark.parametrize(('data', 'expected'), [
    (True, True),
    (False, False),
    (1, True),
    (0, False),
    ('t', True),
    ('T', True),
    ('f', False),
    ('F', False),
    ('true', True),
    ('True', True),
    ('TRUE', True),
    ('false', False),
    ('False', False),
    ('FALSE', False),
    ('y', True),
    ('Y', True),
    ('n', False),
    ('N', False),
    ('yes', True),
    ('Yes', True),
    ('YES', True),
    ('no', False),
    ('No', False),
    ('No', False),
    ('1', True),
    ('0', False),
])
def test_to_internal_value(data, expected):
    assert BooleanField().to_internal_value(data) is expected


@pytest.mark.parametrize('data', [
    123.456,
    '1.0',
    {'foo': 1, 'bar': 2},
    ['foo', 'bar', 'baz'],
])
def test_to_internal_value_invalid(data):
    print data

    with pytest.raises(ValidationError):
        BooleanField().to_internal_value(data)
