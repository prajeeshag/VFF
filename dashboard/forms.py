from django import forms

from django.utils.translation import ugettext_lazy as _

from myapp.widgets import ImageInput

from core.validators import validate_phone_number
from users.models import PlayerProfile


class EditPlayerForm(forms.ModelForm):

    class Meta:
        model = PlayerProfile
        fields = ['first_name', 'last_name', 'dob',
                  'address', 'pincode', 'student',
                  'occupation', 'prefered_foot',
                  'favorite_position', 'height',
                  'weight']


class PhoneNumberForm(forms.Form):
    phone_number = forms.CharField(max_length=10, min_length=10, validators=[
                                   validate_phone_number, ])
