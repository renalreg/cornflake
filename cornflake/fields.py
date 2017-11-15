import collections
import copy
import uuid
from datetime import date, datetime

import six

from cornflake.utils import parse_datetime
from cornflake.exceptions import ValidationError, SkipField


class _empty(object):
    def __nonzero__(self):
        return False


empty = _empty()
try:
    basestring
except NameError:
    basestring = str


class Field(object):
    _creation_counter = 0

    error_messages = {
        'required': 'This field is required.',
    }

    def __new__(cls, *args, **kwargs):
        instance = super(Field, cls).__new__(cls)
        instance._args = args
        instance._kwargs = kwargs
        return instance

    def __init__(
            self,
            source=None, field_name=None,
            read_only=False, write_only=False,
            required=None, default=None, default_empty=empty,
            validators=None, error_messages=None,
            initial=None
    ):
        # Keep track of field declaration order
        self._creation_counter = Field._creation_counter
        Field._creation_counter += 1

        if required is None:
            required = not read_only

        if default_empty is empty:
            default_empty = default

        if validators is None:
            validators = list()

        assert not (read_only and write_only)
        assert not (required and read_only)

        self.source = source
        self.field_name = field_name
        self.required = required
        self.default = default
        self.default_empty = default_empty
        self.read_only = read_only
        self.write_only = write_only
        self.validators = validators
        self.initial = initial

        messages = dict()

        for cls in reversed(self.__class__.__mro__):
            messages.update(getattr(cls, 'error_messages', dict()))

        if error_messages is not None:
            messages.update(error_messages)

        self.error_messages = messages

        self.field_name = None
        self.parent = None

        self._context = {}

    def bind(self, parent, field_name=None):
        self.parent = parent

        if self.field_name is None:
            self.field_name = field_name

        if self.source is None:
            self.source = field_name

    def fail(self, key):
        raise ValidationError(self.error_messages[key])

    @property
    def context(self):
        return self.root._context

    def get_attribute(self, instance):
        try:
            if isinstance(instance, collections.Mapping):
                instance = instance[self.source]
            else:
                instance = getattr(instance, self.source)
        except (AttributeError, KeyError) as e:
            if not self.required:
                raise SkipField

            raise e

        return instance

    def get_value(self, data):
        return data.get(self.field_name, empty)

    def get_default(self, empty):
        if empty:
            default = self.default_empty
        else:
            default = self.default

        if callable(default):
            default = default()

        return default

    def get_initial(self):
        initial = self.initial

        if callable(initial):
            initial = initial()

        return initial

    def to_representation(self, value):
        return value

    def to_internal_value(self, data):
        return data

    def validate_empty_values(self, data):
        if data is empty:
            data = self.get_default(True)
        elif data is None:
            data = self.get_default(False)

        if data is None and self.required:
            self.fail('required')

        return data

    def run_validation(self, data):
        data = self.validate_empty_values(data)

        if data is None:
            return data

        value = self.to_internal_value(data)
        value = self.run_validators(value)
        value = self.validate(value)

        return value

    def run_validators(self, value):
        for validator in self.validators:
            if hasattr(validator, 'set_context'):
                validator.set_context(self)

            try:
                value = validator(value)
            except SkipField:
                break

        return value

    def validate(self, value):
        return value

    @property
    def root(self):
        root = self

        while root.parent is not None:
            root = root.parent

        return root

    def __deepcopy__(self, memo):
        args = copy.deepcopy(self._args)
        kwargs = copy.deepcopy(self._kwargs)
        return self.__class__(*args, **kwargs)


class StringField(Field):
    error_messages = {
        'invalid': 'A valid string is required.'
    }

    def __init__(self, **kwargs):
        self.trim_whitespace = kwargs.pop('trim_whitespace', True)
        super(StringField, self).__init__(**kwargs)

    def to_internal_value(self, data):
        if isinstance(data, (dict, list, bool)):
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

        try:
            value = float(data)
        except (ValueError, TypeError):
            self.fail('invalid')

        return value

    def to_representation(self, value):
        return float(value)


class DateField(Field):
    error_messages = {
        'invalid': 'Invalid date format.',
        'datetime': 'Expected a date but got a datetime.',
    }

    def parse(self, data):
        return parse_datetime(data).date()

    def format(self, value):
        return value.isoformat()

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
                value = self.parse(data)
            except ValueError:
                self.fail('invalid')

            return value

    def to_representation(self, value):
        return self.format(value)


class DateTimeField(Field):
    error_messages = {
        'invalid': 'Invalid date format.',
        'date': 'Expected a datetime but got a date.',
    }

    def parse(self, data):
        return parse_datetime(data)

    def format(self, value):
        return value.isoformat()

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
                value = self.parse(data)
            except ValueError:
                self.fail('invalid')

            return value

    def to_representation(self, value):
        return self.format(value)


class ListField(Field):
    child = None

    error_messages = {
        'not_a_list': 'Expected a list.'
    }

    def __init__(self, *args, **kwargs):
        self.child = kwargs.pop('child', copy.deepcopy(self.child))
        assert self.child is not None

        kwargs.setdefault('default', list)

        super(ListField, self).__init__(*args, **kwargs)

        self.child.bind(self)

    def to_internal_value(self, data):
        if not isinstance(data, list):
            self.fail('not_a_list')

        values = []
        errors = {}

        for i, x in enumerate(data):
            try:
                value = self.child.run_validation(x)
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
            if value is None:
                data.append(None)
            else:
                data.append(self.child.to_representation(value))

        return data


class CommaSeparatedField(Field):
    child = None

    error_messages = {
        'invalid': 'A valid string is required.'
    }

    def __init__(self, **kwargs):
        self.child = kwargs.pop('child', copy.deepcopy(self.child))
        assert self.child is not None

        kwargs.setdefault('default', list)

        super(CommaSeparatedField, self).__init__(**kwargs)

        self.child.bind(self)

    def to_internal_value(self, data):
        if isinstance(data, dict) or isinstance(data, bool):
            self.fail('invalid')

        if isinstance(data, list):
            parts = data
        else:
            data = six.text_type(data)

            if len(data) == 0:
                parts = []
            else:
                parts = data.split(',')

        values = []

        for part in parts:
            value = self.child.run_validation(part)
            values.append(value)

        return values

    def to_representation(self, values):
        data = []

        for value in values:
            if value is None:
                data.append(None)
            else:
                data.append(six.text_type(self.child.to_representation(value)))

        data = ','.join(data)

        return data


class UUIDField(Field):
    error_messages = {
        'invalid': 'A valid UUID is required.'
    }

    def to_internal_value(self, data):
        if isinstance(data, dict) or isinstance(data, list) or isinstance(data, bool):
            self.fail('invalid')

        value = six.text_type(data)

        try:
            value = six.text_type(uuid.UUID(value))
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

    def __init__(self, items, key_field=None, key_name='key', value_name='value', **kwargs):
        super(LookupField, self).__init__(**kwargs)

        if key_field is None:
            key_field = Field()

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
        kwargs['key_field'] = StringField()
        super(StringLookupField, self).__init__(items, **kwargs)


class IntegerLookupField(LookupField):
    def __init__(self, items, **kwargs):
        kwargs['key_field'] = IntegerField()
        super(IntegerLookupField, self).__init__(items, **kwargs)


class EnumLookupField(LookupField):
    def __init__(self, enum, items, **kwargs):
        kwargs['key_field'] = EnumField(enum)
        super(EnumLookupField, self).__init__(items, **kwargs)
