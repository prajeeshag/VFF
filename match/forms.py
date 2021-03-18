
from django import forms
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError
from django.db.models import Q

from core.forms import ListTextWidget

from . import models
from users.models import PlayerProfile, ClubProfile


class EditSubForm(forms.ModelForm):
    class Meta:
        model = models.Substitution
        fields = ['sub_in', 'sub_out', 'reason', 'time']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        squad = self.instance.squad

        sub_in_players = PlayerProfile.objects.none()
        sub_in_player = PlayerProfile.objects.filter(
            pk=self.instance.sub_in.pk)
        sub_in_players = (
            sub_in_player | squad.get_onbench_squad().players.all()).distinct()

        sub_out_players = PlayerProfile.objects.none()
        sub_out_player = PlayerProfile.objects.filter(
            pk=self.instance.sub_out.pk)
        sub_out_players = (
            sub_out_player | squad.get_playing_squad().players.exclude(pk=self.instance.sub_in.pk)).distinct()

        self.fields['sub_in'].queryset = sub_in_players
        self.fields['sub_out'].queryset = sub_out_players


class EditGoalForm(forms.ModelForm):
    class Meta:
        model = models.Goal
        fields = ['own', 'club', 'player', 'attr', 'time']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        match = self.instance.match
        self.fields['club'].queryset = match.get_clubs()
        self.fields['player'].queryset = match.get_match_players().distinct()


class EditCardForm(forms.ModelForm):
    class Meta:
        model = models.Cards
        fields = ['player', 'reason', 'color', 'time']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        match = self.instance.match
        club = self.instance.club
        self.fields['player'].queryset = match.get_match_players(
            club).distinct()
