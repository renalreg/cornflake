import collections
from datetime import date, datetime
import copy
import uuid

import six
import delorean


empty = object()


class ValidationError(Exception):
    def __init__(self, errors):
        self.errors = ValidationError.normalise(errors)

    @staticmethod
    def normalise(errors):
        if isinstance(errors, dict):
            new_errors = {}

            for k, v in errors.items():
                if isinstance(v, dict) or isinstance(v, list):
                    v = ValidationError.normalise(v)
                else:
                    v = [v]

                new_errors[k] = v
        elif isinstance(errors, list):
            new_errors = []

            for x in errors:
                if isinstance(x, dict) or isinstance(x, list):
                    x = ValidationError.normalise(x)

                new_errors.append(x)
        else:
            new_errors = [errors]

        return new_errors

    @staticmethod
    def _first(errors):
        r = None

        if isinstance(errors, list):
            for x in errors:
                r = ValidationError._first(x)

                if r is not None:
                    break
        elif isinstance(errors, dict):
            for k, v in errors.items():
                r = ValidationError._first(v)

                if r is not None:
                    if r[0] is None:
                        path = (k,)
                    else:
                        path = (k,) + r[0]

                    r = (path, r[1])
                    break
        else:
            r = (None, errors)

        return r

    def first(self):
        return ValidationError._first(self.errors)

    def __str__(self):
        return str(self.errors)


class SkipField(Exception):
    pass


class Field(object):
    _creation_counter = 0

    error_messages = {
        'required': 'This field is required.',
        'null': 'This field may not be null.'
    }

    def __init__(self, source=None, read_only=False, write_only=False, required=None, default=empty, validators=None, null=False, error_messages=None):
        # Keep track of field declaration order
        self._creation_counter = Field._creation_counter
        Field._creation_counter += 1

        if required is None:
            required = default is empty and not read_only

        if validators is None:
            validators = list()

        assert not (read_only and write_only)
        assert not (required and read_only)
        assert not (required and default is not empty)

        self.source = source
        self.required = required
        self.default = default
        self.read_only = read_only
        self.write_only = write_only
        self.validators = validators
        self.null = null

        messages = dict()

        for cls in reversed(self.__class__.__mro__):
            messages.update(getattr(cls, 'error_messages', dict()))

        if error_messages is not None:
            messages.update(error_messages)

        self.error_messages = messages

        self.field_name = None
        self.parent = None

    def bind(self, parent, field_name=None):
        self.field_name = field_name
        self.parent = parent

        if self.source is None:
            self.source = field_name

    def fail(self, key):
        raise ValidationError(self.error_messages[key])

    def get_attribute(self, instance):
        try:
            if isinstance(instance, collections.Mapping):
                instance = instance[self.source]
            else:
                instance = getattr(instance, self.source)
        except (AttributeError, KeyError) as e:
            if not self.required and self.default is empty:
                raise SkipField()

            raise e

        return instance

    def get_value(self, data):
        return data.get(self.field_name, empty)

    def get_default(self):
        default = self.default

        if default is empty:
            raise SkipField()

        if callable(default):
            default = default()

        return default

    def to_representation(self, value):
        raise NotImplementedError

    def to_internal_value(self, data):
        raise NotImplementedError

    def validate_empty_values(self, data):
        if self.read_only:
            return (True, self.get_default())

        if data is empty:
            if self.required:
                self.fail('required')

            return (True, self.get_default())

        if data is None:
            if not self.null:
                self.fail('null')

            return (True, None)

        return (False, data)

    def run_validation(self, data):
        (is_empty, data) = self.validate_empty_values(data)

        if is_empty:
            return data

        value = self.to_internal_value(data)
        value = self.run_validators(value)

        return value

    def run_validators(self, value):
        for validator in self.validators:
            value = validator(value)

        return value

    @property
    def root(self):
        root = self

        while root.parent is not None:
            root = root.parent

        return root


class StringField(Field):
    error_messages = {
        'invalid': 'A valid string is required.'
    }

    def __init__(self, **kwargs):
        self.trim_whitespace = kwargs.pop('trim_whitespace', True)
        super(StringField, self).__init__(**kwargs)

    def to_internal_value(self, data):
        if isinstance(data, dict) or isinstance(data, list) or isinstance(data, bool):
            self.fail('invalid')

        value = six.text_type(data)

        if self.trim_whitespace:
            value = value.strip()

        return value

    def to_representation(self, value):
        return six.text_type(value)


class BooleanField(Field):
    error_messages = {
        'invalid': 'A valid boolean is required.'
    }

    TRUE_VALUES = {'t', 'true', 'y', 'yes', '1', 1, True}
    FALSE_VALUES = {'f', 'false', 'n', 'no', '0', 0, False}

    def to_internal_value(self, data):
        if hasattr(data, 'lower'):
            data = data.lower()

        # Check for TypeError as list and dict aren't hashable
        try:
            if data in self.TRUE_VALUES:
                return True
            elif data in self.FALSE_VALUES:
                return False
            else:
                self.fail('invalid')
        except TypeError:
            self.fail('invalid')

    def to_representation(self, value):
        return bool(value)


class IntegerField(Field):
    error_messages = {
        'invalid': 'A valid integer is required.'
    }

    def to_internal_value(self, data):
        if isinstance(data, basestring):
            data = data.strip()

            if len(data) == 0:
                self.fail('invalid')

        try:
            value = int(data)
            value_f = float(data)

            # No floats
            if value != value_f:
                self.fail('invalid')
        except (ValueError, TypeError):
            self.fail('invalid')

        return value

    def to_representation(self, value):
        return int(value)


class FloatField(Field):
    error_messages = {
        'invalid': 'A valid number is required.'
    }

    def to_internal_value(self, data):
        if isinstance(data, basestring):
            data = data.strip()

            if len(data) == 0:
                self.fail('invalid')

        try:
            value = float(data)
        except (ValueError, TypeError):
            self.fail('invalid')

        return value

    def to_representation(self, value):
        return float(value)


class DateField(Field):
    error_messages = {
        'invalid': 'Date has wrong format.',
        'datetime': 'Expected a date but got a datetime.',
    }

    def to_internal_value(self, data):
        if isinstance(data, datetime):
            self.fail('datetime')
        elif isinstance(data, date):
            # Already a date
            return data
        elif not isinstance(data, six.string_types):
            # Not a string
            self.fail('invalid')
        else:
            try:
                value = delorean.parse(data).date
            except ValueError:
                self.fail('invalid')

            return value

    def to_representation(self, value):
        return value.isoformat()


class DateTimeField(Field):
    error_messages = {
        'invalid': 'Datetime has wrong format.',
        'date': 'Expected a date but got a datetime.',
    }

    def to_internal_value(self, data):
        if isinstance(data, datetime):
            # Already a datetime
            return data
        elif isinstance(data, date):
            self.fail('date')
        elif not isinstance(data, six.string_types):
            # Not a string
            self.fail('invalid')
        else:
            try:
                value = delorean.parse(data).datetime
            except ValueError:
                self.fail('invalid')

            return value

    def to_representation(self, value):
        return value.isoformat()


class ListField(Field):
    child_field = None

    error_messages = {
        'not_a_list': 'Expected a list.'
    }

    def __init__(self, *args, **kwargs):
        self.child_field = kwargs.pop('child_field', copy.deepcopy(self.child_field))
        assert self.child is not None
        super(ListField, self).__init__(*args, **kwargs)
        self.child_field.bind(self)

    def to_internal_value(self, data):
        if not isinstance(data, list):
            self.fail('not_a_list')

        values = []
        errors = {}

        for i, x in enumerate(data):
            try:
                value = self.child_field.to_internal_value(x)
            except ValidationError as e:
                errors[i] = e.errors
            else:
                values.append(value)

        if errors:
            raise ValidationError(errors)

        return values

    def to_representation(self, values):
        data = []

        for value in values:
            data.append(self.child_field.to_representation(value))

        return data


class CommaSeparatedField(Field):
    child_field = None

    error_messages = {
        'invalid': 'A valid string is required.'
    }

    def __init__(self, field, **kwargs):
        self.child = kwargs.pop('child_field', copy.deepcopy(self.child_field))
        assert self.child_field is not None
        super(CommaSeparatedField, self).__init__(**kwargs)
        self.child_field.bind(self)

    def to_internal_value(self, data):
        if isinstance(data, dict) or isinstance(data, list) or isinstance(data, bool):
            self.fail('invalid')

        parts = six.text_type(data).split(',')
        values = []

        for part in parts:
            value = self.child_field.to_value(part)
            values.append(value)

        return values

    def to_representation(self, values):
        return ','.join(six.text_type(value) for value in values)


class UUIDField(Field):
    error_messages = {
        'invalid': 'A valid UUID is required.'
    }

    def to_internal_value(self, data):
        if isinstance(data, dict) or isinstance(data, list) or isinstance(data, bool):
            self.fail('invalid')

        value = six.text_type(data)

        try:
            uuid.UUID(data)
        except ValueError:
            self.fail('invalid')

        return value

    def to_representation(self, value):
        return six.text_type(value)


class EnumField(Field):
    error_messages = {
        'invalid': 'Not a valid value.'
    }

    def __init__(self, enum, **kwargs):
        super(EnumField, self).__init__(**kwargs)
        self.enum = enum

    def to_internal_value(self, data):
        try:
            value = self.enum(data)
        except ValueError:
            self.fail('invalid')

        return value

    def to_representation(self, value):
        try:
            data = value.value
        except AttributeError:
            data = value

        return data


class LookupField(Field):
    error_messages = {
        'invalid': 'Not a valid value.'
    }

    def __init__(self, key_field, items, key_name='key', value_name='value', **kwargs):
        super(LookupField, self).__init__(**kwargs)

        self.key_field = key_field
        self.key_field.bind(self)

        self.value_field = StringField()
        self.value_field.bind(self)

        self.items = items

        self.key_name = key_name
        self.value_name = value_name

    def to_internal_value(self, data):
        if isinstance(data, dict):
            data = data.get(self.key_name, empty)

            if data is empty:
                self.fail('required')
            elif data is None:
                if None in self.items:
                    value = data
                else:
                    self.fail('required')
            else:
                value = self.key_field.to_internal_value(data)
        else:
            value = self.key_field.to_internal_value(data)

        if value not in self.items.keys():
            self.fail('invalid')

        return value

    def to_representation(self, key):
        value = self.items[key]

        return {
            self.key_name: self.key_field.to_representation(key),
            self.value_name: self.value_field.to_representation(value)
        }


class StringLookupField(LookupField):
    def __init__(self, items, **kwargs):
        key_field = StringField()
        super(StringLookupField, self).__init__(key_field, items, **kwargs)


class IntegerLookupField(LookupField):
    def __init__(self, items, **kwargs):
        key_field = IntegerField()
        super(IntegerLookupField, self).__init__(key_field, items, **kwargs)


class EnumLookupField(LookupField):
    def __init__(self, enum, items, **kwargs):
        key_field = EnumField(enum)
        super(EnumLookupField, self).__init__(key_field, items, **kwargs)


class JSONField(Field):
    def to_internal_value(self, data):
        return data

    def to_representation(self, value):
        return value
