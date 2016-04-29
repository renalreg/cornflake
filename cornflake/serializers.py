import copy

from cornflake.fields import Field, ValidationError, SkipField, empty


class BaseSerializer(Field):
    def __init__(self, instance=None, data=None, **kwargs):
        meta = getattr(self, 'Meta', None)

        if meta is not None:
            default_validators = getattr(meta, 'validators', None)

            if default_validators is not None and kwargs.get('validators') is None:
                kwargs['validators'] = default_validators

        super(BaseSerializer, self).__init__(**kwargs)

        if data is None:
            data = dict()

        self.instance = instance
        self.initial_data = data

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


class Serializer(BaseSerializer):
    error_messages = {
        'not_a_dict': 'Expected an object.'
    }

    def get_fields(self):
        # TODO
        return {}

    @property
    def fields(self):
        fields = self.get_fields()

        for field_name, field in fields.items():
            field.bind(self, field_name)

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

    def validate(self, value):
        return value

    def to_internal_value(self, data):
        if not isinstance(data, dict):
            self.fail('not_a_list')

        errors = {}
        value = {}

        for field in self.writable_fields:
            field_value = field.get_value(data)
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
        data = dict()

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
    child_serializer = None

    default_error_messages = {
        'not_a_list': 'Expected a list.'
    }

    def __init__(self, *args, **kwargs):
        self.child_serializer = kwargs.pop('child_serializer', copy.deepcopy(self.child_serializer))
        assert self.child_serializer is not None
        super(ListSerializer, self).__init__(*args, **kwargs)
        self.child_serializer.bind(self)

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
                value = self.child_serializer.to_internal_value(x)
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
            data.append(self.child_serializer.to_representation(value))

        return data

    def create(self, validated_data):
        return [self.child_serializer.create(value) for value in validated_data]
