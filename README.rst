# Cornflake

[![Build Status](https://img.shields.io/travis/renalreg/cornflake.svg)](https://travis-ci.org/renalreg/cornflake) [![Code Climate](https://img.shields.io/codeclimate/github/renalreg/cornflake.svg)](https://codeclimate.com/github/renalreg/cornflake) [![Coveralls](https://img.shields.io/coveralls/renalreg/cornflake.svg)](https://coveralls.io/github/renalreg/cornflake)

Cornflake is a serialization library inspired by [Django REST Framework](http://www.django-rest-framework.org/).

## Usage

First we create a serializer and a class to test it with:

```python
from cornflake import fields
from cornflake import serializers
from cornflake.exceptions import ValidationError
from cornflake.validators import not_empty, not_in_future

class PatientSerializer(serializers.Serializer):
    first_name = fields.StringField(validators=[not_empty()])
    last_name = fields.StringField(validators=[not_empty()])
    birth_date = fields.DateField(validators=[not_in_future()])
    death_date = fields.DateField(required=False)

    def validate_first_name(self, value):
        if value.upper() == 'TEST':
            raise ValidationError('No test patients please.')

        return value

    def validate(self, data):
        if data['death_date'] is not None and data['death_date'] < data['birth_date']:
            raise ValidationError({'death_date': "Can't be before birth date."})

        return data

    def create(self, validated_data):
        return Patient(**validated_data)

    def update(self, instance, validated_data):
        for key, value in validated_data.items():
            setattr(instance, key, value)

        return instance

class Patient(object):
    def __init__(self, first_name, last_name, birth_date, death_date):
        self.first_name = first_name
        self.last_name = last_name
        self.birth_date = birth_date
        self.death_date = death_date
```

Now we can create a patient:

```python
>>> serializer = PatientSerializer(data={'first_name': 'John', 'last_name': 'Smith', 'birth_date': '2001-02-03'})
>>> serializer.is_valid()
True
>>> patient = serializer.save()
```

Update the patient with new data:

```python
>>> serializer = PatientSerializer(patient, data={'first_name': 'John', 'last_name': 'Smith', 'birth_date': '2001-02-03', 'death_date': '2016-01-01'})
>>> serializer.is_valid()
True
>>> patient = serializer.save()
```

Serialize the patient to use in an API response:

```python
>>> serializer = PatientSerializer(patient)
>>> serializer.data
{'birth_date': '2001-02-03', 'first_name': u'John', 'last_name': u'Smith', 'death_date': '2016-01-01'}
```

Deserialize, validate and report errors:

```python
>>> serializer = PatientSerializer(data={'first_name': 'TEST', 'last_name': 'Smith', 'birth_date': '2001-02-03'})
>>> serializer.is_valid()
False
>>> serializer.errors
{'first_name': ['No test patients please.']}
```

## Tests

Run tests with the `tox` command:

```
pip install tox
tox
```
