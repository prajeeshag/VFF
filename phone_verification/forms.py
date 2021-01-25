
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from core.validators import validate_phone_number
from django.utils.module_loading import import_string
from .backends import get_backend


class PhoneVerificationForm(forms.Form):
    key = 'phone_verification'
    timeout_error = False
    phone_number = forms.CharField(
        max_length=10, min_length=10, label=_('Phone number'),
        required=False, help_text=_('Enter your 10 digit phone number'))

    def __init__(self, request, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request
        if self.is_bound:
            self.fields['otp'] = forms.CharField(
                max_length=10, label=_('OTP'), required=False,
                help_text=_('Enter the OTP recieved in your phone'))
        else:
            sess = self.request.session.get(self.key, default=None)
            if sess:
                self.request.session.pop(self.key)

    def clean(self):
        data = super().clean()
        phone_number = data.get('phone_number')
        otp = data.get('otp')
        sess = self.request.session.get(self.key, default=None)
        phone_number_in_session = None
        if sess:
            phone_number_in_session = sess.get('number', None)

        if not phone_number_in_session:
            try:
                validate_phone_number(phone_number)
            except ValidationError as e:
                del self.fields['otp']
                raise e
            backend = get_backend()
            del self.fields['phone_number']
            self.request.session[self.key] = {'number': phone_number}
        else:
            del self.fields['phone_number']

        if not otp or otp == '':
            raise ValidationError('Enter the OTP send to your phone')

        backend = get_backend()
        phone_number = self.request.session[self.key]['number']
        res = backend.validate_security_code(phone_number, otp)
        if res == backend.SECURITY_CODE_INVALID:
            raise ValidationError(
                _("Invalid OTP: Enter the correct OTP"), code='invalid_otp')
        if res == backend.SECURITY_CODE_NOTFOUND:
            self.timeout_error = True
            self.fields['phone_number'] = forms.CharField(
                max_length=10, min_length=10, label=_('Phone number'),
                required=False, help_text=_('Enter your 10 digit phone number'))
            del self.fields['otp']
            raise ValidationError(
                _("Timeout: Enter your phone number to try again"), code='timeout')

    def clean_phone_number(self):
        sess = self.request.session.get(self.key, default=None)
        phone_number_in_session = None
        if sess:
            phone_number_in_session = sess.get('number', None)

        if not phone_number_in_session:
            raise ValidationError(_("Unknown error happened!"))

        return phone_number_in_session
