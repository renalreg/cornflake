import copy
from collections import OrderedDict

import six

from cornflake.fields import Field, empty
from cornflake.exceptions import ValidationError, SkipField


class BaseSerializer(Field):
    def __init__(self, instance=None, data=None, **kwargs):
        meta = getattr(self, 'Meta', None)

        if meta is not None:
            default_validators = getattr(meta, 'validators', None)

            if default_validators is not None and kwargs.get('validators') is None:
                kwargs['validators'] = default_validators

        context = kwargs.pop('context', None)

        super(BaseSerializer, self).__init__(**kwargs)

        if data is None:
            data = {}

        self.instance = instance
        self.initial_data = data

        if context is not None:
            self._context = context

        self.errors = {}
        self.validated_data = {}

    def is_valid(self, raise_exception=False):
        try:
            self.validated_data = self.run_validation(self.initial_data)
        except ValidationError as e:
            self.validated_data = {}
            self.errors = e.errors
        else:
            self.errors = {}

        if self.errors and raise_exception:
            raise ValidationError(self.errors)

        return not bool(self.errors)

    @property
    def data(self):
        if self.instance is not None:
            data = self.to_representation(self.instance)
        elif self.validated_data:
            data = self.to_representation(self.validated_data)
        else:
            data = {}

        return data

    def create(self, validated_data):
        raise NotImplementedError

    def update(self, instance, validated_data):
        raise NotImplementedError

    def save(self, **kwargs):
        validated_data = dict(
            list(self.validated_data.items()) +
            list(kwargs.items())
        )

        if self.instance is None:
            self.instance = self.create(validated_data)
        else:
            self.instance = self.update(self.instance, validated_data)

        return self.instance


class SerializerMetaclass(type):
    def __new__(cls, name, bases, attrs):
        attrs['_declared_fields'] = SerializerMetaclass.get_fields(bases, attrs)
        return super(SerializerMetaclass, cls).__new__(cls, name, bases, attrs)

    @staticmethod
    def get_fields(bases, attrs):
        fields = []

        # Get the fields declared on this class
        for field_name, obj in list(attrs.items()):
            if isinstance(obj, Field):
                fields.append((field_name, attrs.pop(field_name)))

        # Sort the fields in the order they were declared
        fields.sort(key=lambda x: x[1]._creation_counter)

        # Loop in reverse to maintain correct field ordering
        for serializer_class in reversed(bases):
            if hasattr(serializer_class, '_declared_fields'):
                # Copy fields from another serializer
                # Parent serializer's fields go first
                fields = list(serializer_class._declared_fields.items()) + fields
            else:
                # Copy fields from mixins
                mixin_fields = SerializerMetaclass.get_mixin_fields(serializer_class).items()

                # Sort the mixin fields in the order they were declared
                mixin_fields.sort(key=lambda x: x[1]._creation_counter)

                # Add the mixin fields
                fields = mixin_fields + fields

        return OrderedDict(fields)

    @staticmethod
    def get_mixin_fields(field_class):
        fields = {}

        for field_mixin_klass in reversed(field_class.__bases__):
            fields.update(SerializerMetaclass.get_mixin_fields(field_mixin_klass))

        for field_name, obj in field_class.__dict__.items():
            if isinstance(obj, Field):
                fields[field_name] = obj

        return fields


@six.add_metaclass(SerializerMetaclass)
class Serializer(BaseSerializer):
    error_messages = {
        'not_a_dict': 'Expected an object.'
    }

    def get_fields(self):
        return copy.deepcopy(self._declared_fields)

    @property
    def fields(self):
        fields = self.get_fields()

        for field_name, field in fields.items():
            field.bind(self, field_name)
            setattr(self, field_name, field)

        return fields

    @property
    def writable_fields(self):
        return [
            field for field in self.fields.values()
            if not field.read_only or field.default is not empty
        ]

    @property
    def readable_fields(self):
        return [
            field for field in self.fields.values()
            if not field.write_only
        ]

    def run_validation(self, data):
        value = self.to_internal_value(data)

        try:
            value = self.run_validators(value)
            value = self.validate(value)
        except ValidationError as e:
            if isinstance(e.errors, dict):
                raise
            else:
                raise ValidationError({'_': e.errors})

        return value

    def pre_validate(self, value):
        return value

    def validate(self, value):
        return value

    def run_field_validators(self, data, field, validators):
        value = field.get_attribute(data)

        try:
            for validator in self.validators:
                if hasattr(validator, 'set_context'):
                    validator.set_context(self)

                value = validator(value)
        except ValidationError as e:
            raise ValidationError({field.field_name: e.errors})

        data[field.source] = value

    def to_internal_value(self, data):
        if not isinstance(data, dict):
            self.fail('not_a_dict')

        errors = {}
        field_values = {}

        for field in self.writable_fields:
            field_values[field.field_name] = field.get_value(data)

        field_values = self.pre_validate(field_values)

        value = {}

        for field in self.writable_fields:
            field_value = field_values[field.field_name]
            validate_method = getattr(self, 'validate_' + field.field_name, None)

            try:
                field_value = field.run_validation(field_value)

                if validate_method is not None:
                    field_value = validate_method(field_value)
            except ValidationError as e:
                errors[field.field_name] = e.errors
            except SkipField:
                pass
            else:
                value[field.source] = field_value

        if errors:
            raise ValidationError(errors)

        return value

    def to_representation(self, instance):
        data = {}

        for field in self.readable_fields:
            try:
                attribute = field.get_attribute(instance)
            except SkipField:
                continue

            if attribute is None:
                data[field.field_name] = None
            else:
                data[field.field_name] = field.to_representation(attribute)

        return data


class ListSerializer(BaseSerializer):
    child = None

    default_error_messages = {
        'not_a_list': 'Expected a list.'
    }

    def __init__(self, *args, **kwargs):
        self.child = kwargs.pop('child', copy.deepcopy(self.child))
        assert self.child is not None
        super(ListSerializer, self).__init__(*args, **kwargs)
        self.child.bind(self)

    def run_validation(self, data):
        value = self.to_internal_value(data)

        try:
            value = self.run_validators(value)
            value = self.validate(value)
        except ValidationError as e:
            if isinstance(e.errors, dict):
                raise
            else:
                raise ValidationError({'_': e.errors})

        return value

    def validate(self, value):
        return value

    def to_internal_value(self, data):
        if not isinstance(data, list):
            self.fail('not_a_list')

        values = []
        errors = {}

        for i, x in enumerate(data):
            try:
                value = self.child.to_internal_value(x)
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
            data.append(self.child.to_representation(value))

        return data

    def create(self, validated_data):
        return [self.child.create(value) for value in validated_data]
