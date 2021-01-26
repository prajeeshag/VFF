from django import forms
from django

from django.utils.translation import ugettext_lazy as _


from . import models


class PlayerProfileForm(forms.ModelForm):
    class Meta:
        model = models.PlayerProfile
        fields = ['first_name', 'last_name', 'dob',
                  'address', 'pincode', 'student',
                  'occupation']
