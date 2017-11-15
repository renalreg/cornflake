import re
from datetime import datetime, date
try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse

import bleach
import pytz

from cornflake.fields import ValidationError, SkipField
from cornflake.utils import is_date, date_to_datetime, safe_strftime

HUMAN_DATE_FORMAT = '%d/%m/%Y'

EMAIL_REGEX = re.compile(r'^\S+@[^\.@\s][^@]*\.[^\.@\s]+$')
EMAIL_NAME_REGEX = re.compile(r'^.* <\S+@[^\.@\s][^@]*\.[^\.@\s]+>$')

POSTCODE_BFPO_REGEX = re.compile('^BFPO[ ]?\\d{1,4}$')
POSTCODE_REGEX = re.compile('^(GIR[ ]?0AA|((AB|AL|B|BA|BB|BD|BH|BL|BN|BR|BS|BT|BX|CA|CB|CF|CH|CM|CO|CR|CT|CV|CW|DA|DD|DE|DG|DH|DL|DN|DT|DY|E|EC|EH|EN|EX|FK|FY|G|GL|GY|GU|HA|HD|HG|HP|HR|HS|HU|HX|IG|IM|IP|IV|JE|KA|KT|KW|KY|L|LA|LD|LE|LL|LN|LS|LU|M|ME|MK|ML|N|NE|NG|NN|NP|NR|NW|OL|OX|PA|PE|PH|PL|PO|PR|RG|RH|RM|S|SA|SE|SG|SK|SL|SM|SN|SO|SP|SR|SS|ST|SW|SY|TA|TD|TF|TN|TQ|TR|TS|TW|UB|W|WA|WC|WD|WF|WN|WR|WS|WV|YO|ZE)(\\d[\\dA-Z]?[ ]?\\d[ABD-HJLN-UW-Z]{2}))|BFPO[ ]?\\d{1,4})$')  # noqa

TAB_TO_SPACE_REGEX = re.compile('\t')
NORMALISE_WHITESPACE_REGEX = re.compile(r'\s{2,}')


def required():
    def required_f(value):
        if value is None:
            raise ValidationError('This field is required.')

        return value

    return required_f


def optional():
    def optional_f(value):
        if value is None:
            raise SkipField()

        return value

    return optional_f


def none_if_blank():
    def none_if_blank_f(value):
        if len(value) == 0:
            value = None

        return value

    return none_if_blank_f


def not_empty():
    def not_empty_f(value):
        if value is None or len(value) == 0:
            raise ValidationError('This field is required.')

        return value

    return not_empty_f


def min_(min_value, units=None):
    if units is None:
        message = 'Must be greater than or equal to %s.'
    else:
        message = 'Must be greater than or equal to %%s %s.' % units

    def min_f(value):
        if value < min_value:
            raise ValidationError(message % min_value)

        return value

    return min_f


def max_(max_value, units=None):
    if units is None:
        message = 'Must be less than or equal to %s.'
    else:
        message = 'Must be less than or equal to %%s %s.' % units

    def max_f(value):
        if value > max_value:
            raise ValidationError(message % max_value)

        return value

    return max_f


def range_(min_value=None, max_value=None, units=None):
    def range_f(value):
        if min_value is not None:
            value = min_(min_value, units)(value)

        if max_value is not None:
            value = max_(max_value, units)(value)

        return value

    return range_f


def in_(values):
    def in_f(value):
        if value not in values:
            raise ValidationError('Not a valid value.')

        return value

    return in_f


def not_in_future():
    def not_in_future_f(value):
        if is_date(value):
            now = date.today()
        else:
            now = datetime.now(pytz.utc)

        if value > now:
            raise ValidationError("Can't be in the future.")

        return value

    return not_in_future_f


def after(min_dt, dt_format=HUMAN_DATE_FORMAT):
    if is_date(min_dt):
        min_dt = date_to_datetime(min_dt)

    def after_f(value):
        if is_date(value):
            value_dt = date_to_datetime(value)
        else:
            value_dt = value

        if value_dt < min_dt:
            raise ValidationError('Value is before %s.' % safe_strftime(min_dt, dt_format))

        return value

    return after_f


def before(max_dt, dt_format=HUMAN_DATE_FORMAT):
    if is_date(max_dt):
        max_dt = date_to_datetime(max_dt)

    def before_f(value):
        if is_date(value):
            value_dt = date_to_datetime(value)
        else:
            value_dt = value

        if value_dt > max_dt:
            raise ValidationError('Value is after %s.' % safe_strftime(max_dt, dt_format))

        return value

    return before_f


def max_length(max_value):
    def max_length_f(value):
        if len(value) > max_value:
            raise ValidationError('Value is too long (max length is %d characters).' % max_value)

        return value

    return max_length_f


def min_length(min_value):
    def min_length_f(value):
        if len(value) < min_value:
            raise ValidationError('Value is too short (min length is %d characters).' % min_value)

        return value

    return min_length_f


def email_address(name=False):
    def email_address_f(value):
        value = value.lower()

        if not EMAIL_REGEX.match(value) and (not name or not EMAIL_NAME_REGEX.match(value)):
            raise ValidationError('Not a valid email address.')

        return value

    return email_address_f


def postcode():
    def postcode_f(value):
        value = value.upper()
        value = re.sub('[^A-Z0-9]', '', value)

        if not POSTCODE_REGEX.match(value):
            raise ValidationError('Not a valid postcode.')

        if POSTCODE_BFPO_REGEX.match(value):
            value = value[:-4] + ' ' + value[-4:]
        else:
            value = value[:-3] + ' ' + value[-3:]

        return value

    return postcode_f


def normalise_whitespace():
    def normalise_whitespace_f(value):
        # Tabs to spaces
        value = TAB_TO_SPACE_REGEX.sub(' ', value)

        # Multiple spaces
        value = NORMALISE_WHITESPACE_REGEX.sub(' ', value)

        return value

    return normalise_whitespace_f


def upper():
    def upper_f(value):
        value = value.upper()
        return value

    return upper_f


def lower():
    def lower_f(value):
        value = value.lower()
        return value

    return lower_f


def url():
    def url_f(value):
        result = urlparse(value)

        if not result.scheme:
            raise ValidationError('No scheme.')

        if not result.netloc:
            raise ValidationError('No network location.')

        return value

    return url_f


def sanitize_html():
    def sanitize_html_f(value):
        value = bleach.clean(
            value,
            tags=['a', 'b', 'br', 'em', 'i', 'li', 'ol', 'p', 'strong', 'ul', 'div'],
            attributes={
                'a': ['href', 'target']
            }
        )

        return value

    return sanitize_html_f


def call_me_maybe(x):
    try:
        return x()
    except TypeError:
        return x


def default(default_value):
    def default_f(value):
        if value is None:
            value = call_me_maybe(default_value)

        return value

    return default_f


def default_now():
    return default(lambda: datetime.now(tz=pytz.UTC))
