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
