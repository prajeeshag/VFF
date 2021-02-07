import humanize

from django.db import models, transaction

from model_utils.models import StatusModel, TimeStampedModel
from model_utils import Choices

from django.conf import settings
from django.utils import timezone
from django.urls import reverse_lazy, reverse, path, include

from users.models import PlayerProfile, ClubProfile
from fixture.models import Matches


NFIRST = 7
NSUB = 8
MATCHTIME = 40


class NotMyMatch(Exception):
    pass


class NoteModel(models.Model):
    text = models.CharField(max_length=100, unique=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.text


class MatchTimeLine(TimeStampedModel, StatusModel):
    STATUS = Choices('active', 'inactive')
    status = models.CharField(
        max_length=20, choices=STATUS, default=STATUS.active)
    match = models.OneToOneField(Matches, on_delete=models.PROTECT)
    first_half_start = models.DateTimeField(null=True)
    first_half_end = models.DateTimeField(null=True)
    second_half_start = models.DateTimeField(null=True)
    second_half_end = models.DateTimeField(null=True)

    class AlreadyStartedError(Exception):
        pass

    class AlreadyEndedError(Exception):
        pass

    def __str__(self):
        return "{} timeline".format(self.match)

    def get_absolute_url(self):
        return reverse('match:matchtimeline', kwargs={'pk': self.pk})

    def score_as_string(self):
        return Goal.score_as_string(self.match)

    def get_time_string(self, evtime=None):
        halftime = int(MATCHTIME/2)
        time = None
        if self.second_half_start:
            time = self.second_half_start
            offset = halftime
        elif self.first_half_start:
            time = self.first_half_start
            offset = 0

        if not time:
            if evtime:
                return ""
            return (humanize.naturalday(self.match.date)
                    + " " + timezone.localtime(self.match.date).strftime('%I:%M %p'))

        if self.second_half_end:
            return 'FT'

        stime = evtime
        if not stime:
            stime = timezone.now()

        diff = stime - time
        minute = (diff.days*24*60) + (diff.seconds/60)
        minute = int(minute)
        addl = max(0, minute-halftime)
        minute = offset + minute - addl
        minutec = "{}'".format(minute)
        if addl > 0:
            minutec = "{}+{}'".format(minutec, addl)
        return minutec

    def start_first_half(self):
        if self.first_half_start:
            raise self.AlreadyStartedError
        self.first_half_start = timezone.now()
        self.save()
        Events.objects.create(
            time=timezone.now(),
            matchtimeline=self,
            label='Kick off',
            side=Events.SIDE.neutral,
            kind=Events.KIND.other,
        )

    def start_second_half(self):
        if self.second_half_start:
            raise self.AlreadyStartedError
        self.second_half_start = timezone.now()
        self.save()
        sublabel = Goal.score_as_string(self.match)
        Events.objects.create(
            time=timezone.now(),
            matchtimeline=self,
            label='Second half begins',
            sublabel=sublabel,
            side=Events.SIDE.neutral,
            kind=Events.KIND.other,
        )

    def end_first_half(self):
        if self.first_half_end:
            raise self.AlreadyEndedError
        self.first_half_end = timezone.now()
        self.save()
        sublabel = Goal.score_as_string(self.match)
        Events.objects.create(
            time=timezone.now(),
            matchtimeline=self,
            label='Half Time',
            sublabel=sublabel,
            side=Events.SIDE.neutral,
            kind=Events.KIND.other,
        )

    def finalize_match(self):
        if self.second_half_end:
            raise self.AlreadyEndedError

        with transaction.atomic():
            # set suspension completed (if any) for players who was not in squad
            Suspension.set_completed_for_match(match)

            # Finalize Cards
            Cards.finalize_match(self.match)
            self.second_half_end = timezone.now()
            self.save()

            sublabel = Goal.score_as_string(self.match)
            Events.objects.create(
                time=timezone.now(),
                matchtimeline=self,
                label='Full Time',
                sublabel=sublabel,
                side=Events.SIDE.neutral,
                kind=Events.KIND.other,
            )


class Events(TimeStampedModel):
    SIDE = Choices('neutral', 'home', 'away')
    KIND = Choices('sub', 'yellowcard', 'redcard', 'lineup',  'goal', 'other')
    matchtimeline = models.ForeignKey(MatchTimeLine, on_delete=models.PROTECT)
    kind = models.CharField(
        max_length=20, choices=KIND, default=KIND.other)
    side = models.CharField(max_length=20, choices=SIDE, default=SIDE.neutral)
    label = models.CharField(max_length=64)
    sublabel = models.CharField(max_length=128, blank=True)
    time = models.DateTimeField(default=timezone.now)
    url = models.CharField(max_length=200, null=True)
    time_label = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return self.label

    def get_time_string(self):
        return self.matchtimeline.get_time_string(evtime=self.time)

    def save(self, *args, **kwargs):
        self.time_label = self.get_time_string()
        super().save(*args, **kwargs)


class EventMixin:
    event_label = None
    event_sublabel = None
    event_label_field = None
    event_sublabel_field = None
    event_time_field = 'time'

    class EventTimeNotAvailable(Exception):
        pass

    class EventLabelNotAvailable(Exception):
        pass

    class EventMatchNotAvailable(Exception):
        pass

    class EventClubNotAvailable(Exception):
        pass

    def get_event_label(self):
        if self.event_label:
            return self.event_label
        elif self.event_label_field:
            return getattr(self, self.event_label_field)
        else:
            raise self.EventLabelNotAvailable

    def get_event_sublabel(self):
        if self.event_sublabel:
            return self.event_sublabel
        elif self.event_sublabel_field:
            return getattr(self, self.event_sublabel_field)
        else:
            return ""

    def get_match(self):
        if hasattr(self, 'match') and self.match:
            return self.match
        else:
            return None

    def get_club(self):
        if hasattr(self, 'club') and self.club:
            return self.club
        else:
            return None

    def get_event_kind(self):
        if hasattr(self, 'event_kind'):
            return self.event_kind
        return Events.KIND.other

    def get_event_side(self):
        match = self.get_match()
        club = self.get_club()
        side = Events.SIDE.neutral
        if match and club:
            side = Events.SIDE.home
            if match.away == club:
                side = Events.SIDE.away
        return side

    def get_event_url(self):
        if hasattr(self, 'get_absolute_url'):
            return self.get_absolute_url()
        else:
            return None

    def get_event_time(self):
        if hasattr(self, 'time') and self.time:
            return self.time
        else:
            raise self.EventTimeNotAvailable

    def create_timeline_event(self):
        match = self.get_match()
        if not match:
            self.EventMatchNotAvailable
        timeline, created = MatchTimeLine.objects.get_or_create(match=match)
        side = self.get_event_side()
        label = self.get_event_label()
        sublabel = self.get_event_sublabel()
        time = self.get_event_time()
        url = self.get_event_url()
        kind = self.get_event_kind()
        Events.objects.create(
            matchtimeline=timeline,
            kind=kind,
            side=side,
            label=label,
            sublabel=sublabel,
            url=url,
            time=time,
        )


class Squad(StatusModel, TimeStampedModel, EventMixin):
    KIND = Choices('parent', 'first', 'bench', 'playing',
                   'onbench', 'avail', 'suspen')
    STATUS = Choices('pre', 'final', 'approved')
    event_label = 'Line Up'
    event_kind = Events.KIND.lineup
    kind = models.CharField(
        max_length=10, choices=KIND, default=KIND.parent)
    match = models.ForeignKey(
        Matches, on_delete=models.PROTECT, null=True, related_name='squad')
    club = models.ForeignKey(ClubProfile, on_delete=models.PROTECT, null=True)
    players = models.ManyToManyField(PlayerProfile, related_name='squads')
    parent = models.ForeignKey(
        'self', on_delete=models.PROTECT, null=True, related_name='items')
    time = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    class Meta:
        unique_together = ['club', 'match']

    class LimitReached(Exception):
        pass

    class GotSuspension(Exception):
        pass

    def __str__(self):
        if self.parent:
            return '{} ({})'.format(self.parent, self.kind)
        else:
            return '{} squad for {}'.format(self.club.abbr.upper(), self.match)

    def is_pre(self):
        return self.status == self.STATUS.pre

    def is_final(self):
        return self.status == self.STATUS.final

    def is_approved(self):
        return self.status == self.STATUS.approved

    @ classmethod
    def _create_parent(cls, created_by, club, match):
        if not match.is_playing(club):
            raise NotMyMatch

        return cls.objects.create(
            kind=cls.KIND.parent,
            created_by=created_by,
            club=club,
            match=match,
            status=cls.STATUS.pre,
        )

    @ classmethod
    def _create_onbench(cls, parent):
        return cls.objects.create(kind=cls.KIND.onbench, parent=parent)

    @ classmethod
    def _create_first(cls, parent):
        return cls.objects.create(kind=cls.KIND.first, parent=parent)

    @ classmethod
    def _create_playing(cls, parent):
        return cls.objects.create(kind=cls.KIND.playing, parent=parent)

    @ classmethod
    def _create_bench(cls, parent):
        return cls.objects.create(kind=cls.KIND.bench, parent=parent)

    @ classmethod
    def _create_avail(cls, parent):
        return cls.objects.create(kind=cls.KIND.avail, parent=parent)

    @ classmethod
    def _create_suspen(cls, parent):
        return cls.objects.create(kind=cls.KIND.suspen, parent=parent)

    @ classmethod
    def create(cls, match, club, user):
        parent = None
        with transaction.atomic():
            parent = cls._create_parent(
                created_by=user, club=club, match=match)
            cls._create_first(parent)
            cls._create_bench(parent)
            cls._create_playing(parent)
            cls._create_onbench(parent)
            avail = cls._create_avail(parent)
            suspen = cls._create_suspen(parent)
            for player in club.get_players():
                if Suspension.has_suspension(player):
                    suspen.players.add(player)
                else:
                    avail.players.add(player)

        return parent

    @ classmethod
    def get_squad(cls, match, club):
        return cls.objects.get(match=match, club=club)

    def get_first_squad(self):
        return self.items.filter(kind=self.KIND.first).first()

    def get_bench_squad(self):
        return self.items.filter(kind=self.KIND.bench).first()

    def get_onbench_squad(self):
        return self.items.filter(kind=self.KIND.onbench).first()

    def get_playing_squad(self):
        return self.items.filter(kind=self.KIND.playing).first()

    def get_avail_squad(self):
        return self.items.filter(kind=self.KIND.avail).first()

    def get_suspen_squad(self):
        return self.items.filter(kind=self.KIND.suspen).first()

    def get_first_players(self):
        return self.get_first_squad().players.all()

    def get_bench_players(self):
        return self.get_bench_squad().players.all()

    def get_onbench_players(self):
        return self.get_onbench_squad().players.all()

    def get_playing_players(self):
        return self.get_playing_squad().players.all()

    def get_suspen_players(self):
        return self.get_suspen_squad().players.all()

    def get_avail_players(self):
        return self.get_avail_squad().players.all()

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
        if not self.match.is_player_playing(player):
            raise NotMyMatch

        self.get_first_squad().players.add(player)
        self.get_playing_squad().players.add(player)
        self.get_avail_squad().players.remove(player)

    def add_player_to_bench(self, player):
        if self.get_bench_players().count() >= NSUB:
            raise self.LimitReached
        if Suspension.has_suspension(player):
            raise self.GotSuspension
        if not self.match.is_player_playing(player):
            raise NotMyMatch
        self.get_bench_squad().players.add(player)
        self.get_onbench_squad().players.add(player)
        self.get_avail_squad().players.remove(player)

    def remove_player_from_playing(self, player):
        self.get_playing_squad().players.remove(player)

    def remove_player_from_onbench(self, player):
        self.get_onbench_squad().players.remove(player)

    def remove_player_from_first(self, player):
        self.get_first_squad().players.remove(player)
        self.get_playing_squad().players.remove(player)
        self.get_avail_squad().players.add(player)

    def remove_player_from_bench(self, player):
        self.get_bench_squad().players.remove(player)
        self.get_onbench_squad().players.remove(player)
        self.get_avail_squad().players.add(player)

    def get_available_players(self):
        return self.get_avail_players()

    def finalize(self):
        self.status = self.STATUS.final
        self.save()
        self.create_timeline_event()

    def substitute(self, playerin, playerout, user, reason_text=None):
        self.get_playing_squad().players.remove(playerout)
        self.get_playing_squad().players.add(playerin)
        self.get_onbench_squad().players.remove(playerin)
        reason = None
        if reason_text:
            reason = SubstitutionReason.objects.get_or_create(text=reason_text)
        obj = Substitution.objects.create(
            squad=self, created_by=user,
            sub_in=playerin, sub_out=playerout,
            reason=reason)
        obj.create_timeline_event()
        return obj

    def get_absolute_url(self):
        return reverse('match:squad', kwargs={'pk': self.pk})


class CardReason(NoteModel):
    pass


class Cards(TimeStampedModel, StatusModel):
    STATUS = Choices('submitted', 'approved')
    COLOR = Choices('red', 'yellow')
    event_label_field = 'player'
    event_sublabel_field = 'reason'
    event_time_field = 'time'
    color = models.CharField(
        max_length=10, choices=COLOR, default=COLOR.yellow)
    match = models.ForeignKey(Matches, on_delete=models.PROTECT)
    player = models.ForeignKey(PlayerProfile, on_delete=models.CASCADE)
    time = models.DateTimeField(default=timezone.now)
    reason = models.ForeignKey(
        CardReason,
        on_delete=models.PROTECT,
        null=True)

    class Meta:
        unique_together = ['player', 'match']

    class GotRedAlready(Exception):
        pass

    def get_event_kind(self):
        return self.color

    def get_club(self):
        return self.player.get_club()

    @classmethod
    def get_all_reds(cls, match):
        return cls.objects.filter(match=match, color=cls.COLOR.red)

    @classmethod
    def get_all_yellow(cls, match):
        return cls.objects.filter(match=match, color=cls.COLOR.yellow)

    @classmethod
    def finalize_match(cls, match):
        # Red cards
        for card in cls.get_all_reds(match):
            reason = SuspensionReason.objects.get_or_create(text='Red card')
            Suspension.create(card.player, reason)

        # Yellow cards
        for card in cls.get_all_yellow(match):
            player = card.player
            accu, created = AccumulatedCards.objects.get_or_create(
                player=player)
            accu.add_yellow()

    @classmethod
    def raise_red_card(cls, match, player, reason_text):
        cls.objects.filter(match=match, player=player).delete()
        reason = CardReason.objects.get_or_create(text=reason_text)
        obj = cls.objects.create(
            match=match, player=player, color=cls.COLOR.red, reason=reason)
        obj.create_timeline_event()

    @classmethod
    def raise_yellow_card(cls, match, player, reason_text):
        red = cls.objects.filter(
            match=match, player=player, color=cls.COLOR.red).first()
        if red:
            raise cls.GotRedAlready

        yellow1 = cls.objects.filter(
            match=match, player=player, color=cls.COLOR.yellow).first()

        reason = CardReason.objects.get_or_create(text=reason_text)
        obj = cls.objects.create(
            match=match, player=player, color=cls.COLOR.yellow, reason=reason)

        obj.create_timeline_event()
        if yellow1:
            reason1 = CardReason.objects.get_or_create(text='second yellow')
            cls.raise_red_card(match, player, reason1)


class SubstitutionReason(NoteModel):
    pass


class Substitution(models.Model):
    event_kind = Events.KIND.sub
    squad = models.ForeignKey(Squad, on_delete=models.PROTECT)
    sub_in = models.ForeignKey(
        PlayerProfile, on_delete=models.PROTECT, related_name='sub_ins')
    sub_out = models.ForeignKey(
        PlayerProfile, on_delete=models.PROTECT, related_name='sub_outs')
    time = models.DateTimeField(default=timezone.now)
    reason = models.ForeignKey(
        SubstitutionReason,
        on_delete=models.PROTECT,
        null=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    def get_club(self):
        return self.sub_in.get_club()

    def get_match(self):
        return self.squad.match

    def get_event_label(self):
        return "In: {}".format(self.sub_in)

    def get_event_sublabel(self):
        sublabel = "Out: {}".format(self.sub_out)
        if not self.reason:
            return sublabel
        return "{} ({})".format(sublabel, self.reason)

    def get_absolute_url(self):
        return None


class GoalAttr(NoteModel):
    pass


class Goal(StatusModel, TimeStampedModel, EventMixin):
    event_kind = Events.KIND.goal
    STATUS = Choices('submitted', 'approved')
    own = models.BooleanField(default=False)
    time = models.DateTimeField(default=timezone.now)
    player = models.ForeignKey(
        PlayerProfile, on_delete=models.SET_NULL, null=True, related_name='goals')
    club = models.ForeignKey(
        ClubProfile, on_delete=models.PROTECT, related_name='goals')
    match = models.ForeignKey(
        Matches, on_delete=models.PROTECT, related_name='goals')
    attr = models.ForeignKey(
        GoalAttr, on_delete=models.PROTECT, null=True, related_name='goals')

    def __str__(self):
        strng = "Goal: {}".format(self.player)
        if self.own:
            return "Goal(own): {}".format(self.player)

    def get_event_label(self):
        strng = "Goal: {}".format(self.player)
        if self.own:
            return "Goal (own)".format(self.player)

    def get_event_sublabel(self):
        if self.own:
            return self.player
        return self.attr

    def save(self, *args, **kwargs):
        if self.own:
            self.club = self.match.get_opponent_team_of_player(player)
        else:
            self.club = player.get_club()
        super().save(*args, **kwargs)

    @classmethod
    def score(cls, match):
        return (cls.objects.filter(match=match, club=match.home).count(),
                cls.objects.filter(match=match, club=match.away).count(),)

    @classmethod
    def score_as_string(cls, match):
        home, away = cls.score(match)
        return "{} - {}".format(home, away)


class SuspensionReason(NoteModel):
    pass


class Suspension(StatusModel, TimeStampedModel):
    STATUS = Choices('pending', 'completed', 'canceled')
    player = models.ForeignKey(PlayerProfile, on_delete=models.CASCADE)
    reason = models.ForeignKey(SuspensionReason, on_delete=models.PROTECT)

    class SuspensionExist(Exception):
        pass

    @classmethod
    def has_suspension(cls, player):
        return cls.pending.filter(player=player).exists()

    @classmethod
    def create(cls, player, reason):
        return cls.pending.create(player=player, reason=reason)

    @classmethod
    def set_completed(cls, player):
        susp = cls.pending.filter(player).first()
        if susp:
            susp.status = cls.STATUS.completed
            susp.save()

    @classmethod
    def set_completed_for_match(cls, match):
        for players in Squad.get_squad(match, match.home).get_suspen_players():
            cls.set_completed(player)
        for players in Squad.get_squad(match, match.away).get_suspen_players():
            cls.set_completed(player)


class AccumulatedCards(TimeStampedModel):
    player = models.OneToOneField(PlayerProfile, on_delete=models.CASCADE)
    yellow = models.PositiveIntegerField(default=0)

    def add_yellow(self):
        self.yellow += 1
        if self.yellow > 2:
            reason = SuspensionReason.objects.get_or_create(
                text='Yellow card ban')
            Suspension.create(player, reason)
            self.yellow = 0
        self.save()
