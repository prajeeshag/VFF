
from django import forms
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError

from core.forms import ListTextWidget


from match.models import MATCHTIME


class EmptyForm(forms.Form):
    pass


class DateTimeForm(forms.Form):
    time = forms.DateTimeField(label='Date and Time')


class MatchTimeForm(forms.Form):
    ftime = forms.IntegerField(
        min_value=1, max_value=200, initial=0,
        label='Match time (in minutes)')
    stime = forms.IntegerField(
        min_value=0, max_value=200, initial=0,
        label='Additional time (in minutes)')

    def __init__(self, timeline, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.half = 'notstart'
        if timeline.first_half_start:
            self.half = 'first'
        if timeline.second_half_start:
            self.half = 'second'

    def clean(self):
        data = super().clean()
        ftime = data.get('ftime')
        stime = data.get('stime')
        halftime = int(MATCHTIME/2)
        fulltime = MATCHTIME
        if self.half == 'second':
            if ftime <= halftime or ftime > fulltime:
                raise ValidationError(
                    'Wrong Match timings 1!')
            if stime > 0 and ftime < fulltime:
                raise ValidationError(
                    'Wrong Match timings 2!')
        elif self.half == 'first':
            if ftime > halftime:
                raise ValidationError(
                    'Wrong Match timings 3!')
            if stime > 0 and ftime < halftime:
                raise ValidationError(
                    'Wrong Match timings 4!')
        else:
            raise ValidationError('Wrong Match timings, Match not started!')


class PlayerSelectFormOnspot(forms.Form):
    player = forms.ModelChoiceField(queryset=None, required=True)
    attr = forms.CharField(label='Attributes', max_length=100)

    def __init__(self, qattrs, qplayers, attr_required=True, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['player'].queryset = qplayers
        self.fields['attr'].widget = ListTextWidget(
            data_list=qattrs, name='attr-list',
            attrs={'autocomplete': 'off'})
        self.fields['attr'].required = attr_required


class PlayerSelectForm(DateTimeForm, PlayerSelectFormOnspot):
    pass


class PlayerSelectForm2Onspot(forms.Form):
    player_in = forms.ModelChoiceField(
        label='Sub in', queryset=None, required=True)
    player_out = forms.ModelChoiceField(
        label='Sub out', queryset=None, required=True)
    attr = forms.CharField(label='Attributes', max_length=100, required=False)

    def __init__(self, qattrs, qplayers_in, qplayers_out, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['player_in'].queryset = qplayers_in
        self.fields['player_out'].queryset = qplayers_out
        self.fields['attr'].widget = ListTextWidget(
            data_list=qattrs, name='attr-list',
            attrs={'autocomplete': 'off'})


class PlayerSelectForm2(DateTimeForm, PlayerSelectForm2Onspot):
    pass
