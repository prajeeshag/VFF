from django import forms

from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext_lazy as _
from django.contrib.admin.widgets import AdminDateWidget

from myapp.widgets import ImageInput

from core.validators import validate_phone_number
from users.models import PlayerProfile


class EmailForm(forms.ModelForm):
    title = 'Update email'

    class Meta:
        model = get_user_model()
        fields = ['email', ]

    def clean(self):
        email = self.clean().get('email')
        if email:
            users = get_user_model().objects.filter(email=email)
            if users.exists():
                raise ValidationError(
                    _('This email is already taken'), code='email_taken')


class EditPlayerForm(forms.ModelForm):

    class Meta:
        model = PlayerProfile
        fields = ['name', 'nickname', 'dob', 'address',
                  'pincode', 'student', 'occupation', 'height',
                  'weight', 'prefered_foot', 'favorite_position']


class PhoneNumberForm(forms.Form):
    phone_number = forms.CharField(max_length=10, min_length=10, validators=[
                                   validate_phone_number, ])
