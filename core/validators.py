
from django.core.exceptions import ValidationError


def validate_phone_number(phone):
    if not (phone.isdigit() and len(phone) == 10):
        raise ValidationError('%(phone)s must be 10 digits',
                              params={'phone': phone},)


def validate_Indian_pincode(pin):
    if not (pin.isdigit() and len(pin) == 6):
        raise ValidationError('Invalid pincode')
