
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
        self.fields['sub_in'].queryset = squad.get_onbench_squad().players.all()
        self.fields['sub_out'].queryset = squad.get_playing_squad().players.all()

    def save(self, commit=True):
        initial = self.instance
        current = super().save(commit=False)
        playing_sqd = initial.squad.get_playing_squad()
        onbench_sqd = initial.squad.get_onbench_squad()
        tobench_sqd = initial.squad.get_tobench_squad()

        if current.sub_in != initial.sub_in:
            playing_sqd.remove_player(initial.sub_in)
            onbench_sqd.add_player(initial.sub_in)
            playing_sqd.add_player(current.sub_in)
            onbench_sqd.remove_player(current.sub_in)
        elif current.sub_out != initial.sub_out:
            playing_sqd.add_player(initial.sub_out)
            tobench_sqd.remove_player(initial.sub_out)
            playing_sqd.remove_player(current.sub_out)
            tobench_sqd.add_player(current.sub_out)

        if commit:
            current.save()

        return current


class EditGoalForm(forms.ModelForm):
    class Meta:
        model = models.Goal
        fields = ['own', 'club', 'player', 'attr', 'time']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        match = self.instance.match
        self.fields['club'].queryset = match.get_clubs()
        self.fields['player'].queryset = match.get_played_players().distinct()


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
