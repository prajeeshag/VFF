
from django import forms
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError

from core.forms import ListTextWidget


from match.models import MATCHTIME


class EmptyForm(forms.Form):
    pass


class DateTimeForm(forms.Form):
    time = forms.DateTimeField(label='Date and Time')


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
