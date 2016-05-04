import pytest

from cornflake.fields import JSONField


@pytest.mark.parametrize(('value', 'expected'), [
    (True, True),
    (False, False),
    (123, 123),
    (123.456, 123.456),
    ('foo', 'foo'),
    (['foo', 'bar'], ['foo', 'bar']),
    ({'foo': 'bar'}, {'foo': 'bar'})
])
def test_to_representation(value, expected):
    assert JSONField().to_representation(value) == expected


@pytest.mark.parametrize(('data', 'expected'), [
    (True, True),
    (False, False),
    (123, 123),
    (123.456, 123.456),
    ('foo', 'foo'),
    (['foo', 'bar'], ['foo', 'bar']),
    ({'foo': 'bar'}, {'foo': 'bar'})
])
def test_to_internal_value(data, expected):
    assert JSONField().to_internal_value(data) == expected
