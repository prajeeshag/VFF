
from django import forms
from django.utils.translation import ugettext_lazy as _


class DateTimeForm(forms.Form):
    time = forms.DateTimeField(label='Date and Time')
