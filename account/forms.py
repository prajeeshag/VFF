
from datetime import datetime, timedelta

from django import forms
from django.core.exceptions import ValidationError

from django.utils.translation import ugettext_lazy as _

from phone_verification.forms import PhoneVerificationMixin
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, UsernameField
from django.contrib.auth import get_user_model
from django.conf import settings

from users.models import PhoneNumber
from core.validators import validate_phone_number
from phone_verification.backends import get_backend


class LoginForm(AuthenticationForm):
    username = UsernameField(
        label=_('Username or Phone number'),
        widget=forms.TextInput(attrs={'autofocus': True})
    )


class SignupStep1(PhoneVerificationMixin, forms.ModelForm):

    class Meta:
        model = PhoneNumber
        fields = []

    def clean_phone_number(self):
        data = self.phone_number_clean()
        phone_number = data
        if phone_number:
            try:
                obj = PhoneNumber.objects.get(number=phone_number)
                if hasattr(obj, 'user'):
                    raise ValidationError(
                        _('A user already exist with this phone number!'), code='user_exist')
            except PhoneNumber.DoesNotExist:
                pass
        return data

    def save(self, commit=True):
        phone_number = self.cleaned_data.get('phone_number')
        try:
            obj = PhoneNumber.objects.get(number=phone_number)
            if hasattr(obj, 'user'):
                raise ValidationError(
                    _('A user already exist with this phone number!'), code='user_exist')
            else:
                return obj
        except PhoneNumber.DoesNotExist:
            pass

        obj = super().save(commit=False)
        obj.number = phone_number
        obj.verified = True

        if commit:
            obj.save()
        return obj


class SignupStep2(UserCreationForm):
    User = get_user_model()
    user_type = forms.ChoiceField(
        choices=User.ACCOUNT_TYPE_CHOICES[1:3],
        label=_('Account type'))
    field_order = ['user_type', 'username', 'password1', 'password2']

    class Meta:
        model = get_user_model()
        fields = ['username', 'password1', 'password2']


class PhoneNumberForm(forms.Form):
    phone_number = forms.CharField(
        validators=[validate_phone_number, ],
        max_length=10, min_length=10, label=_('Phone number'),
        required=True, help_text=_('Enter your 10 digit phone number'))


class OtpForm(forms.Form):
    key = '_otp_send_time'
    otp = forms.CharField(
        max_length=10, label=_('OTP'), required=True,
        help_text=_('Enter the OTP recieved in your phone'))

    def __init__(self, phone_number, request, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.phone_number = phone_number
        timestamp = request.session.get(self.key)
        otp_send_time = None
        if timestamp:
            otp_send_time = datetime.fromtimestamp(timestamp)

        if not self.is_bound:
            backend = get_backend()
            if not otp_send_time or (otp_send_time + timedelta(minutes=3)
                                     < datetime.now()):
                backend.send_verification_code(phone_number)
                otp_send_time = datetime.now()
                request.session[self.key] = datetime.timestamp(otp_send_time)
        wait_time = otp_send_time - datetime.now()
        self.wait_time = wait_time.total_seconds()

    def clean(self):
        data = super().clean()
        otp = data.get('otp')
        if otp:
            backend = get_backend()
            code = backend.validate_security_code(self.phone_number, otp)
            if code != backend.SECURITY_CODE_VERIFIED:
                raise ValidationError(_('Invalid Otp'), code='invalid_otp')


class PassWordResetStep1(PhoneNumberForm):
    title = 'Step 1: Enter your phone number'

    def clean(self):
        UserModel = get_user_model()
        data = super().clean()
        phone_number = data.get('phone_number')
        if phone_number:
            try:
                user = UserModel.objects.filter(
                    phone_number__number=phone_number).distinct()
            except UserModel.DoesNotExist:
                raise ValidationError(
                    _('User with this phone number does not exist'), code='user_not_exist')
            if not user.exists():
                raise ValidationError(
                    _('User with this phone number does not exist'), code='user_not_exist')


class PassWordResetStep2(OtpForm):
    title = 'Step 2: Enter OTP'


class PassWordResetStep3(forms.Form):
    title = 'Step 3: Enter the new Password'
    password1 = forms.CharField(label=_('Enter password'),
                                max_length=50, widget=forms.PasswordInput)
    password2 = forms.CharField(label=_('Enter the same password again'),
                                max_length=50, widget=forms.PasswordInput)

    def clean(self):
        data = super().clean()
        password1 = data.get('password1')
        password2 = data.get('password2')

        if password1 and password2:
            if password1 != password2:
                raise ValidationError(
                    _("Passwords entered doesn't match"), code='password_not_match')
