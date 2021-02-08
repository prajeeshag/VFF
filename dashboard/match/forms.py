
from django import forms
from django.utils.translation import ugettext_lazy as _


class DateTimeForm(forms.Form):
    time = forms.DateTimeField(label='Date and Time')


class MatchTimeForm(forms.Form):
    minutes = forms.IntegerField(
        min_value=0, max_value=200, label='Match time (in minutes)')
