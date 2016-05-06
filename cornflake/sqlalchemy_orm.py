from sqlalchemy.sql import sqltypes
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect
from sqlalchemy.orm import ColumnProperty

from cornflake import fields, serializers


class ModelSerializer(serializers.Serializer):
    type_map = {
        sqltypes.String: fields.StringField,
        sqltypes.Integer: fields.IntegerField,
        sqltypes.BigInteger: fields.IntegerField,
        sqltypes.Date: fields.DateField,
        sqltypes.DateTime: fields.DateTimeField,
        sqltypes.Boolean: fields.BooleanField,
        sqltypes.Numeric: fields.FloatField,
        postgresql.INET: fields.StringField,
        postgresql.UUID: fields.UUIDField,
        postgresql.JSONB: fields.JSONField
    }

    class Meta(object):
        model_class = None

    def get_model_class(self):
        model_class = self.Meta.model_class
        assert model_class is not None
        return model_class

    def get_model_fields(self):
        """ List of model fields to include (defaults to all) """

        model_fields = getattr(self.Meta, 'fields', None)

        if model_fields:
            model_fields = set(model_fields)

        return model_fields

    def get_model_exclude(self):
        """ List of fields to exclude """

        return set(getattr(self.Meta, 'exclude', []))

    def get_model_read_only(self):
        """ Fields that should be read only (serialized but not deserialized) """

        return set(getattr(self.Meta, 'read_only', []))

    def get_model_write_only(self):
        """ Fields that should be write only (deserialized but not serialized) """

        return set(getattr(self.Meta, 'write_only', []))

    def get_field_class(self, col_type):
        for sql_type, field_type in self.type_map.items():
            if isinstance(col_type, sql_type):
                return field_type

        return None

    def get_fields(self):
        fields = super(ModelSerializer, self).get_fields()

        model_fields = self.get_model_fields()
        model_exclude = self.get_model_exclude()
        model_read_only = self.get_model_read_only()
        model_write_only = self.get_model_write_only()

        props = inspect(self.get_model_class()).attrs

        for prop in props:
            if not isinstance(prop, ColumnProperty):
                continue

            key = prop.key

            # Field explicitly defined
            if key in fields:
                continue

            # Not in field list
            if model_fields and key not in model_fields:
                continue

            # Field excluded
            if key in model_exclude:
                continue

            col = prop.columns[0]
            col_type = col.type

            field_kwargs = {}

            # Read only field
            # Don't allow id column to be updated
            # TODO(rupert) default to read only if primary key (remove 'id' check)
            if key in model_read_only or key == 'id':
                field_kwargs['read_only'] = True

            # Write only field
            if key in model_write_only:
                field_kwargs['write_only'] = True

            # Get the field class for this column type
            field_class = self.get_field_class(col_type)

            # This will skip column types we can't handle
            if field_class is not None:
                field = field_class(**field_kwargs)
                field.bind(self, key)
                fields[key] = field

        return fields

    def create(self, validated_data):
        model_class = self.get_model_class()
        instance = model_class()

        for attr, value in validated_data.items():
            if hasattr(instance, attr):
                setattr(instance, attr, value)

        return instance

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            if hasattr(instance, attr):
                setattr(instance, attr, value)

        return instance


class ReferenceField(fields.Field):
    type_map = {
        sqltypes.String: fields.StringField,
        sqltypes.Integer: fields.IntegerField,
        postgresql.UUID: fields.UUIDField,
    }

    error_messages = {
        'not_found': 'Object not found.',
        'no_id': 'No ID supplied.'
    }

    model_class = None

    # TODO(rupert) use Model.id instead, default to getattr(model_class, 'id')
    model_id = 'id'

    serializer_class = None

    def __init__(self, **kwargs):
        self.model_class = kwargs.pop('model_class', self.model_class)
        self.model_id = kwargs.pop('model_id', self.model_id)
        self.serializer_class = kwargs.pop('serializer_class', self.serializer_class)

        assert self.model_class is not None
        assert self.model_id is not None

        super(ReferenceField, self).__init__(**kwargs)

        self.field = self.get_field()
        self.serializer = self.get_serializer()

    def get_serializer(self):
        serializer_class = self.serializer_class

        if serializer_class is not None:
            serializer = serializer_class()
        else:
            serializer = None

        return serializer

    def get_field_class(self):
        prop = getattr(inspect(self.model_class).attrs, self.model_id)
        col = prop.columns[0]
        col_type = col.type

        for sql_type, field_type in self.type_map.items():
            if isinstance(col_type, sql_type):
                return field_type

        return fields.StringField

    def get_field(self):
        return self.get_field_class()()

    def bind(self, parent, field_name=None):
        super(ReferenceField, self).bind(parent, field_name)
        self.field.bind(self, field_name)

        if self.serializer is not None:
            self.serializer.bind(self, field_name)

    def get_instance(self, id):
        instance = self.model_class.query.filter(getattr(self.model_class, self.model_id) == id).first()

        if instance is None:
            self.fail('not_found')

        return instance

    def to_internal_value(self, data):
        if isinstance(data, self.model_class):
            return data

        if isinstance(data, dict):
            value = data.get(self.model_id)

            if value is None:
                self.fail('no_id')

            instance_id = self.field.to_internal_value(value)
        else:
            instance_id = self.field.to_internal_value(data)

        instance = self.get_instance(instance_id)

        return instance

    def to_representation(self, instance):
        if self.serializer is not None:
            return self.serializer.to_representation(instance)
        else:
            instance_id = getattr(instance, self.model_id)
            return self.field.to_representation(instance_id)
