from django.db import models

from django.conf import settings
from django.utils import timezone

from users.models import PlayerProfile, ClubProfile
from fixture.models import Matches


NFIRST = 7
NSUB = 8


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
    match = models.ForeignKey(
        Matches, on_delete=models.PROTECT, null=True, related_name='squad')
    club = models.ForeignKey(ClubProfile, on_delete=models.PROTECT, null=True)
    players = models.ManyToManyField(PlayerProfile, related_name='squads')
    parent = models.ForeignKey(
        'self', on_delete=models.PROTECT, null=True, related_name='items')
    created_time = models.DateTimeField(auto_now_add=True)
    updated_time = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    release = models.BooleanField(default=False)
    timeline = models.BooleanField(editable=False, default=False)

    class Meta:
        unique_together = ['club', 'match']

    class MatchAndClubMismatch(Exception):
        pass

    class LimitReached(Exception):
        pass

    class GotSuspension(Exception):
        pass

    @ classmethod
    def _create_parent(cls, created_by, club, match):
        return cls.objects.create(
            kind=cls.PARENT,
            created_by=created_by,
            club=club,
            match=match
        )

    @ classmethod
    def _create_onbench(cls, parent):
        return cls.objects.create(kind=cls.ONBENCH, parent=parent)

    @ classmethod
    def _create_first(cls, parent):
        return cls.objects.create(kind=cls.FIRST, parent=parent)

    @ classmethod
    def _create_playing(cls, parent):
        return cls.objects.create(kind=cls.PLAYING, parent=parent)

    @ classmethod
    def _create_bench(cls, parent):
        return cls.objects.create(kind=cls.BENCH, parent=parent)

    @ classmethod
    def create(cls, match, club, user):
        parent = cls._create_parent(created_by=user, club=club, match=match)
        cls._create_first(parent)
        cls._create_bench(parent)
        cls._create_playing(parent)
        cls._create_onbench(parent)
        return parent

    @ classmethod
    def get_squad(cls, match, club):
        return cls.objects.get(match=match, club=club)

    def get_first_squad(self):
        return self.items.filter(kind=self.FIRST).first()

    def get_bench_squad(self):
        return self.items.filter(kind=self.BENCH).first()

    def get_onbench_squad(self):
        return self.items.filter(kind=self.ONBENCH).first()

    def get_playing_squad(self):
        return self.items.filter(kind=self.PLAYING).first()

    def get_first_players(self):
        return self.get_first_squad().players.all()

    def get_bench_players(self):
        return self.get_bench_squad().players.all()

    def get_onbench_players(self):
        return self.get_onbench_squad().players.all()

    def get_playing_players(self):
        return self.get_playing_squad().players.all()

    def add_player_to_playing(self, player):
        if self.get_playing_players().count() >= NFIRST:
            raise self.LimitReached
        self.get_playing_squad().players.add(player)

    def add_player_to_onbench(self, player):
        self.get_onbench_squad().players.add(player)

    def add_player_to_first(self, player):
        if self.get_first_players().count() >= NFIRST:
            raise self.LimitReached
        if Suspension.has_suspension(player):
            raise self.GotSuspension
        self.get_first_squad().players.add(player)
        self.get_playing_squad().players.add(player)

    def add_player_to_bench(self, player):
        if self.get_bench_players().count() >= NSUB:
            raise self.LimitReached
        if Suspension.has_suspension(player):
            raise self.GotSuspension
        self.get_bench_squad().players.add(player)
        self.get_onbench_squad().players.add(player)

    def remove_player_from_playing(self, player):
        self.get_playing_squad().players.remove(player)

    def remove_player_from_onbench(self, player):
        self.get_onbench_squad().players.remove(player)

    def remove_player_from_first(self, player):
        self.get_first_squad().players.remove(player)
        self.get_playing_squad().players.add(player)

    def remove_player_from_bench(self, player):
        self.get_bench_squad().players.remove(player)
        self.get_onbench_squad().players.add(player)

    def get_available_players(self):
        first = self.get_first_players()
        bench = self.get_bench_players()
        all_player = self.club.get_players()
        for player in first:
            all_player.remove(player)
        for player in bench:
            all_player.remove(player)

        players = all_player.copy()

        for player in players:
            if Suspension.has_suspension(player):
                all_player.remove(player)

        return all_player

    def finalize(self):
        self.release = True
        self.timeline = True
        self.save()

    def substitute(self, playerin, playerout, user):
        self.get_playing_squad().players.remove(playerout)
        self.get_playing_squad().players.add(playerin)
        self.get_onbench_squad().players.remove(playerin)
        obj = Substitution.objects.create(
            squad=self, created_by=user, sub_in=playerin, sub_out=playerout)
        return obj

    def get_absolute_url(self):
        return reverse('match:squad', kwargs={'pk': self.pk})

    def timeline_url(self):
        return self.get_absolute_url()

    def timeline_time(self):
        return self.updated_time

    def timeline_message(self):
        abbr = self.club.abbr
        abbr = abbr.upper()
        return "{} Lineup".format(abbr)


class Suspension(models.Model):
    YELLOWCARDS = 'yellow'
    REDCARD = 'Red'
    OTHER = 'Other'
    reason_choices = (
        (YELLOWCARDS, YELLOWCARDS),
        (REDCARD, REDCARD),
        (OTHER, OTHER),
    )
    player = models.ForeignKey(PlayerProfile, on_delete=models.CASCADE)
    reason = models.CharField(max_length=20, choices=reason_choices)
    note = models.CharField(max_length=100, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    active = models.BooleanField(default=True)

    class Meta:
        unique_together = ['player', 'created']

    class SuspensionExist(Exception):
        pass

    @classmethod
    def has_suspension(cls, player):
        try:
            return cls.objects.get(player=player, active=True)
        except cls.DoesNotExist:
            return None

    @classmethod
    def create(cls, player, reason):
        return cls.objects.create(player=player, reason=reason)

    @classmethod
    def release(cls, player):
        try:
            obj = cls.objects.get(player=player, active=True)
            obj.active = False
            obj.save()
        except cls.DoesNotExist:
            return


class AccumulatedCards(models.Model):
    player = models.OneToOneField(PlayerProfile, on_delete=models.CASCADE)
    yellow = models.PositiveIntegerField(default=0)

    def add_yellow(self):
        self.yellow += 1
        if self.yellow > 2:
            Suspension.create(player, Suspension.YELLOWCARDS)
            self.yellow = 0
        self.save()


class Cards(models.Model):
    RED = 'red'
    YELLOW = 'yellow'
    color_choice = (
        (RED, RED),
        (YELLOW, YELLOW),
    )
    color = models.CharField(max_length=10, choices=color_choice)
    match = models.ForeignKey(Matches, on_delete=models.PROTECT)
    player = models.ForeignKey(PlayerProfile, on_delete=models.CASCADE)
    time = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ['player', 'match', 'color']

    class GotRedAlready(Exception):
        pass

    @classmethod
    def get_all_reds(cls, match):
        return cls.objects.filter(match=match, color=cls.RED)

    @classmethod
    def get_all_yellow(cls, match):
        return cls.objects.filter(match=match, color=cls.YELLOW)

    @classmethod
    def raise_red_card(cls, match, player):
        cls.objects.filter(match=match, player=player).delete()
        cls.objects.create(match=match, player=player, color=cls.RED)

    @classmethod
    def raise_yellow_card(cls, match, player):

        red = cls.objects.filter(
            match=match, player=player, color=cls.RED).first()
        if red:
            raise cls.GotRedAlready

        yellow1 = cls.objects.filter(
            match=match, player=player, color=cls.YELLOW).first()
        if not yellow:
            cls.objects.create(match=match, player=player, color=cls.YELLOW)
        else:
            cls.raise_red_card(match, player)

    def timeline_url(self):
        return None

    def timeline_time(self):
        return self.time

    def timeline_message(self):
        abbr = self.player.get_club().abbr
        abbr = abbr.upper()
        return "{} card for {} player {}".format(self.color, abbr, self.player)


class MatchTimeLine(models.Model):
    match = models.OneToOneField(Matches, on_delete=models.PROTECT)
    first_half_start = models.DateTimeField(null=True)
    first_half_end = models.DateTimeField(null=True)
    second_half_start = models.DateTimeField(null=True)
    second_half_end = models.DateTimeField(null=True)

    class AlreadyStartedError(Exception):
        pass

    class AlreadyEndedError(Exception):
        pass

    def get_absolute_url(self):
        return reverse('match:matchtimeline', kwargs={'pk': self.pk})

    def start_first_half(self):
        if self.first_half_start:
            raise MatchTimeLine.AlreadyStartedError
        self.first_half_start = timezone.now()
        self.save()
        Events.objects.create(
            time=timezone.now(),
            matchtimeline=self,
            message='Match started'
        )

    def start_second_half(self):
        if self.second_half_start:
            raise MatchTimeLine.AlreadyStartedError
        self.second_half_start = timezone.now()
        self.save()
        Events.objects.create(
            time=timezone.now(),
            matchtimeline=self,
            message='Second half started'
        )

    def end_first_half(self):
        if self.first_half_end:
            raise MatchTimeLine.AlreadyEndedError
        self.first_half_end = timezone.now()
        self.save()
        Events.objects.create(
            time=timezone.now(),
            matchtimeline=self,
            message='End of first half'
        )

    def finalize_match(self):
        if self.second_half_end:
            raise MatchTimeLine.AlreadyEndedError

        with transaction.atomic():
            # Release one suspension(if any) for all players
            for player in self.match.home.get_players():
                Suspension.release(player)

            for player in self.match.away.get_players():
                Suspension.release(player)

            # Red cards
            for card in Cards.get_all_reds(self.match):
                Suspension.create(card.player, Suspension.REDCARD)

            # Yellow cards
            for card in Cards.get_all_yellow(self.match):
                player = card.player
                accu, created = AccumulatedCards.objects.get_or_create(
                    player=player)
                accu.add_yellow()

            self.second_half_end = timezone.now()
            self.save()

            Events.objects.create(
                time=timezone.now(),
                matchtimeline=self,
                message='Final whistle...'
            )


class Events(models.Model):
    matchtimeline = models.ForeignKey(MatchTimeLine, on_delete=models.PROTECT)
    message = models.CharField(max_length=200)
    time = models.DateTimeField(default=timezone.now)
    url = models.CharField(max_length=200, null=True)


class Substitution(models.Model):
    squad = models.ForeignKey(Squad, on_delete=models.PROTECT)
    sub_in = models.ForeignKey(
        PlayerProfile, on_delete=models.PROTECT, related_name='sub_ins')
    sub_out = models.ForeignKey(
        PlayerProfile, on_delete=models.PROTECT, related_name='sub_outs')
    time = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    def timeline_url(self):
        return None

    def timeline_time(self):
        return self.time

    def timeline_message(self):
        return "Substitution: {}(in), {}(out)".format(self.sub_in, self.sub_out)

    def get_absolute_url(self):
        return None
