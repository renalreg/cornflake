import collections
from collections import OrderedDict


class ValidationError(Exception):
    def __init__(self, errors):
        self.errors = ValidationError.normalise(errors)

    @staticmethod
    def normalise(errors):
        if isinstance(errors, dict):
            new_errors = OrderedDict()

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

    @staticmethod
    def _flatten(errors, path=None):
        flattened_errors = []

        if path is None:
            path = tuple()

        for field_name, field_errors in errors.items():
            field_path = path + (field_name,)

            if isinstance(field_errors, collections.Mapping):
                flattened_field_errors = ValidationError._flatten(field_errors, path=field_path)
                flattened_errors.extend(flattened_field_errors)
            else:
                for field_error in field_errors:
                    flattened_errors.append((field_path, field_error))

        return flattened_errors

    def flatten(self):
        return ValidationError._flatten(self.errors)

    def __str__(self):
        return str(self.errors)


class SkipField(Exception):
    pass
