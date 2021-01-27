
from datetime import datetime, timedelta

from django import forms
from django.core.exceptions import ValidationError

from django.utils.translation import ugettext_lazy as _

from phone_verification.forms import PhoneVerificationMixin
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, UsernameField
from django.contrib.auth import get_user_model
from django.conf import settings

from users.models import PhoneNumber, PlayerProfile, ProfilePicture, Document
from core.validators import validate_phone_number
from phone_verification.backends import get_backend


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


class LoginForm(AuthenticationForm):
    username = UsernameField(
        label=_('Username or Phone number'),
        widget=forms.TextInput(attrs={'autofocus': True})
    )


class PlayerProfileForm(forms.ModelForm):
    title = _('Create Profile')

    class Meta:
        model = PlayerProfile
        exclude = ('club', 'phone_number',
                   'profilepicture', 'documents', 'user')


class ProfilePictureForm(forms.ModelForm):
    title = _('Upload a profile picture')

    class Meta:
        model = ProfilePicture
        fields = ['image', ]


class DocumentForm1(forms.ModelForm):
    title = _('Upload Photo ID proof')

    class Meta:
        model = Document
        fields = ['image', ]


class DocumentForm2(forms.ModelForm):
    title = _('Upload a Age proof')

    class Meta:
        model = Document
        fields = ['image', ]


class SignupStep1(PhoneNumberForm):
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
                return

            if user.exists():
                raise ValidationError(
                    _('A User with this phone number already exist'), code='user_exist')


class SignupStep2(OtpForm):
    title = 'Step 2: Enter OTP'


class SignupStep3(UserCreationForm):
    User = get_user_model()
    user_type = forms.ChoiceField(
        choices=User.ACCOUNT_TYPE_CHOICES[1:4],
        label=_('Account type'))
    field_order = ['user_type', 'username', 'password1', 'password2']

    class Meta:
        model = get_user_model()
        fields = ['username', 'password1', 'password2']


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
