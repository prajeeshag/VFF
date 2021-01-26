
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _


def validate_phone_number(phone):
    if not (phone.isdigit() and len(phone) == 10):
        raise ValidationError(_('Enter a 10 digit phone number'))


def validate_Indian_pincode(pin):
    if not (pin.isdigit() and len(pin) == 6):
        raise ValidationError('Invalid pincode')
