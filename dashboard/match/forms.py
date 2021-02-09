
from django import forms
from django.utils.translation import ugettext_lazy as _

from core.forms import ListTextWidget

from match.models import MATCHTIME


class DateTimeForm(forms.Form):
    time = forms.DateTimeField(label='Date and Time')


class MatchTimeForm(forms.Form):
    minutes = forms.IntegerField(
        min_value=0, max_value=200, label='Match time (in minutes)')


class PlayerSelectForm(forms.Form):
    time = forms.IntegerField(
        max_value=MATCHTIME, min_value=0, label='Match time (in minutes)')
    attr = forms.CharField(label='Attributes', max_length=100)
    player = forms.ModelChoiceField(queryset=None, required=True)

    def __init__(self, qattrs, qplayers, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['player'].queryset = qplayers
        self.fields['attr'].widget = ListTextWidget(
            data_list=qattrs, name='attr-list')
