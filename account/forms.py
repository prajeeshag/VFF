
from django import forms
from django.core.exceptions import ValidationError

from django.utils.translation import ugettext_lazy as _

from phone_verification.forms import PhoneVerificationMixin
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django.conf import settings

from users.models import PhoneNumber


class SignupStep1(PhoneVerificationMixin, forms.ModelForm):

    class Meta:
        model = PhoneNumber
        fields = []

    def clean_phone_number(self):
        data = self.phone_number_clean()
        phone_number = data
        print('phone_number', data)
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
