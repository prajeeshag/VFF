
from django import forms
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError

from core.forms import ListTextWidget


from match.models import MATCHTIME


class DateTimeForm(forms.Form):
    time = forms.DateTimeField(label='Date and Time')


class MatchTimeForm(forms.Form):
    ftime = forms.IntegerField(
        min_value=0, max_value=200, initial=0,
        label='Match time (in minutes)')
    stime = forms.IntegerField(
        min_value=0, max_value=200, initial=0,
        label='Additional time (in minutes)')

    def clean(self):
        data = super().clean()
        ftime = data.get('ftime')
        stime = data.get('stime')
        if stime > 0 and ftime <= 0:
            raise ValidationError(
                'Match time cannot be 0 when additional time is above 0')


class PlayerSelectForm(MatchTimeForm):
    attr = forms.CharField(label='Attributes', max_length=100)
    player = forms.ModelChoiceField(queryset=None, required=True)

    def __init__(self, qattrs, qplayers, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['player'].queryset = qplayers
        self.fields['attr'].widget = ListTextWidget(
            data_list=qattrs, name='attr-list')
