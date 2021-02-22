
from django import forms
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError
from django.db.models import Q

from core.forms import ListTextWidget

from . import models
from users.models import PlayerProfile, ClubProfile


class EditGoalForm(forms.ModelForm):
    class Meta:
        model = models.Goal
        fields = ['player', 'attr']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        match = self.instance.match
        club = self.instance.club
        if self.instance.own:
            club = self.instance.against
        self.fields['player'].queryset = match.get_played_players(
            club).distinct()


class EditCardForm(forms.ModelForm):
    class Meta:
        model = models.Cards
        fields = ['player', 'reason', 'color']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        match = self.instance.match
        club = self.instance.club
        self.fields['player'].queryset = match.get_played_players(
            club).distinct()
