import uuid

import pytest

from cornflake.fields import UUIDField, ValidationError


@pytest.mark.parametrize(('value', 'expected'), [
    ('8efa76c7-4e42-4424-83bb-fbbc4f758ad1', '8efa76c7-4e42-4424-83bb-fbbc4f758ad1'),
    (uuid.UUID('8efa76c7-4e42-4424-83bb-fbbc4f758ad1'), '8efa76c7-4e42-4424-83bb-fbbc4f758ad1'),
])
def test_to_representation(value, expected):
    assert UUIDField().to_representation(value) == expected


@pytest.mark.parametrize(('data', 'expected'), [
    ('8efa76c7-4e42-4424-83bb-fbbc4f758ad1', '8efa76c7-4e42-4424-83bb-fbbc4f758ad1'),
    ('8EFA76C7-4E42-4424-83BB-FBBC4F758AD1', '8efa76c7-4e42-4424-83bb-fbbc4f758ad1'),
    ('8efa76c74e42442483bbfbbc4f758ad1', '8efa76c7-4e42-4424-83bb-fbbc4f758ad1'),
    (uuid.UUID('8efa76c7-4e42-4424-83bb-fbbc4f758ad1'), '8efa76c7-4e42-4424-83bb-fbbc4f758ad1'),
])
def test_to_internal_value(data, expected):
    assert UUIDField().to_internal_value(data) == expected


@pytest.mark.parametrize('data', [
    '',
    'hello',
    True,
    False,
    {'foo': 1, 'bar': 2},
    ['foo', 'bar', 'baz'],
])
def test_to_internal_value_invalid(data):
    with pytest.raises(ValidationError):
        UUIDField().to_internal_value(data)
