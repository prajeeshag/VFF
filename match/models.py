from django.db import models

from django.conf import settings
from django.utils import timezone

from users.models import PlayerProfile, ClubProfile
from fixture.models import Matches


class Squad(models.Model):
    PARENT = 'PARENT'
    FIRST = 'FIRST'
    BENCH = 'BENCH'
    PLAYING = 'PLAYING'
    ONBENCH = 'ONBENCH'
    kind_choices = (
        (PARENT, PARENT),
        (FIRST, FIRST),
        (BENCH, BENCH),
        (PLAYING, PLAYING),
        (ONBENCH, ONBENCH),
    )
    kind = models.CharField(
        max_length=10, choices=kind_choices, default=PARENT)
    match = models.ForeignKey(Matches, on_delete=models.PROTECT, null=True)
    club = models.ForeignKey(ClubProfile, on_delete=models.PROTECT, null=True)
    players = models.ManyToManyField(PlayerProfile, related_name='squads')
    parent = models.ForeignKey(
        'self', on_delete=models.PROTECT, null=True, related_name='items')
    created_time = models.DateTimeField(auto_now_add=True)
    updated_time = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    class Meta:
        unique_together = ['club', 'match']

    class MatchAndClubMismatch(Exception):
        pass

    @classmethod
    def _create_parent(cls):
        return cls.objects.create(kind=cls.PARENT)

    @classmethod
    def _create_onbench(cls, parent):
        return cls.objects.create(kind=cls.ONBENCH, parent=parent)

    @classmethod
    def _create_first(cls, parent):
        return cls.objects.create(kind=cls.FIRST, parent=parent)

    @classmethod
    def _create_playing(cls, parent):
        return cls.objects.create(kind=cls.PLAYING, parent=parent)

    @classmethod
    def _create_bench(cls, parent):
        return cls.objects.create(kind=cls.BENCH, parent=parent)

    @classmethod
    def create(cls, match, club, user):
        parent = cls._create_parent(created_by=user, club=club, match=match)
        cls._create_first(parent)
        cls._create_bench(parent)
        cls._create_playing(parent)
        cls._create_onbench(parent)
        return parent

    @classmethod
    def get_squad(match, club):
        return cls.objects.get(match=match, club=club)

    def get_first_squad(self):
        return self.items.filter(kind=self.FIRST).first()

    def get_bench_squad(self):
        return self.items.filter(kind=self.BENCH).first()

    def get_onbench_squad(self):
        return self.items.filter(kind=self.ONBENCH).first()

    def get_playing_squad(self):
        return self.items.filter(kind=self.PLAYING).first()

    def add_player_to_first(self, player):
        self.get_first_squad().players.add(player)

    def add_player_to_playing(self, player):
        self.get_playing_squad().players.add(player)

    def add_player_to_onbench(self, player):
        self.get_onbench_squad().players.add(player)

    def add_player_to_bench(self, player):
        self.get_bench_squad().players.add(player)

    def remove_player_to_first(self, player):
        self.get_first_squad().players.remove(player)

    def remove_player_to_playing(self, player):
        self.get_playing_squad().players.remove(player)

    def remove_player_to_onbench(self, player):
        self.get_onbench_squad().players.remove(player)

    def remove_player_to_bench(self, player):
        self.get_bench_squad().players.remove(player)

    def substitute(playerin, playerout):
        self.get_playing_squad().players.remove(playerout)
        self.get_playing_squad().players.add(playerin)
        self.get_onbench_squad().players.remove(playerin)


class Substitution(models.Model):
    squad = models.ForeignKey(Squad, on_delete=models.PROTECT)
    sub_in = models.ForeignKey(
        Player, on_delete=models.PROTECT, related_name='sub_ins')
    sub_out = models.ForeignKey(
        Player, on_delete=models.PROTECT, related_name='sub_outs')
    time = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

