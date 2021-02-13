import humanize
import math

from django.db import models, transaction
from django.conf import settings
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.urls import reverse_lazy, reverse, path, include
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType

from model_utils.models import StatusModel, TimeStampedModel, SoftDeletableModel
from model_utils import Choices

from users.models import PlayerProfile, ClubProfile
from fixture.models import Matches


NFIRST = 7
NSUB = 8
MATCHTIME = 40  # In minutes
NU19 = 1
NU21 = 3
NPLAYERS = 7


def get_time_string(ftime, stime):
    time = math.ceil(ftime/60)
    addl = math.ceil(stime/60)
    if addl > 0:
        return "{}+{}'".format(time, addl)
    if time > 0:
        return "{}'".format(time)
    return ""


def add_num_side_event(side, eventcls):
    """ Add num of events method in a match for a side """
    eventname = eventcls.__name__.lower()
    fn_name = "_".join(['num', side, eventname])

    def fn(self):
        club = getattr(self, side)
        return eventcls.objects.filter(club=club, match=self).count()

    setattr(Matches, fn_name, fn)
    fn.__name__ = fn_name
    fn.__doc__ = "Get # of {} for {} side in {}".format(eventname, side, self)


def add_num_club_event(eventcls):
    """ Add num of events method for club """
    eventname = eventcls.__name__.lower()
    fn_name = "_".join(['num', eventname])

    def fn(self):
        return eventcls.objects.filter(club=self).count()

    setattr(ClubProfile, fn_name, fn)
    fn.__name__ = fn_name
    fn.__doc__ = "Get # of {}".format(eventname)


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
    second_half_start = models.DateTimeField(null=True)
    half_time = models.BooleanField(default=False)
    final_time = models.BooleanField(default=False)

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

    def start_match(self, time=None):
        with transaction.atomic():
            if time:
                self.first_half_start = time
            else:
                self.first_half_start = timezone.now()
            self.save()
            obj = TimeEvents.objects.create(match=self.match,
                                            time=self.first_half_start,
                                            status=TimeEvents.STATUS.kickoff)
            Events.objects.create(
                matchtimeline=self,
                content_object=obj,)

    def start_second_half(self, time=None):
        with transaction.atomic():
            if time:
                self.second_half_start = time
            else:
                self.second_half_start = timezone.now()
            self.save()
            obj = TimeEvents.objects.create(match=self.match,
                                            time=self.second_half_start,
                                            status=TimeEvents.STATUS.second_half)
            Events.objects.create(
                matchtimeline=self,
                content_object=obj,)

    def set_half_time(self, ftime=-1, stime=-1):
        with transaction.atomic():
            score = Goal.score_as_string(self.match)
            obj = TimeEvents.objects.create(
                match=self.match, status=TimeEvents.STATUS.half_time,
                ftime=ftime, stime=stime, sublabel=score)
            self.half_time = True
            self.save()
            Events.objects.create(
                matchtimeline=self,
                content_object=obj,)

    def finalize_match(self, ftime=-1, stime=-1):
        with transaction.atomic():
            score = Goal.score_as_string(self.match)
            obj = TimeEvents.objects.create(
                match=self.match,
                status=TimeEvents.STATUS.final_time,
                ftime=ftime, stime=stime, sublabel=score)
            self.final_time = True
            self.save()

            # set suspension completed (if any) for players who was not in squad
            Suspension.set_completed_for_match(self.match)

            # Finalize Cards
            Cards.finalize_match(self.match)

            Events.objects.create(
                matchtimeline=self,
                content_object=obj,)

            self.match.set_done()


class Events(TimeStampedModel):
    matchtimeline = models.ForeignKey(MatchTimeLine, on_delete=models.PROTECT)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    ftime = models.IntegerField(default=-1)
    stime = models.IntegerField(default=-1)

    class Meta:
        ordering = ['-ftime', '-stime']

    def __str__(self):
        return self.label()

    def kind(self):
        return self.content_object.get_event_kind()

    def side(self):
        return self.content_object.get_event_side()

    def label(self):
        return self.content_object.get_event_label()

    def sublabel(self):
        return self.content_object.get_event_sublabel()

    def url(self):
        return self.content_object.get_event_url()

    def time_label(self):
        return self.content_object.get_event_time_label()

    def save(self, *args, **kwargs):
        self.ftime = self.content_object.ftime
        self.stime = self.content_object.stime
        super().save(*args, **kwargs)


class EventModel(models.Model):
    event_label = None
    event_label_field = None
    event_sublabel = None
    event_sublabel_field = None
    event_time_label = None
    event_side = None
    event_url = None
    event_kind = 'other'

    time = models.DateTimeField(default=timezone.now)
    ftime = models.IntegerField(default=-1)
    stime = models.IntegerField(default=-1)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    timeline_event = GenericRelation(Events)

    class Meta:
        abstract = True

    class EventTimeNotAvailable(Exception):
        pass

    class EventLabelNotAvailable(Exception):
        pass

    class EventMatchNotAvailable(Exception):
        pass

    class EventClubNotAvailable(Exception):
        pass

    def recalc_time(self):
        halftime = int(MATCHTIME*60/2)  # seconds
        fulltime = int(MATCHTIME*60)  # seconds
        match = self.get_match()
        if not match:
            return
        timeline = getattr(match, 'matchtimeline', None)
        if not timeline:
            return

        if timeline.first_half_start and self.time >= timeline.first_half_start:
            tdelta = self.time - timeline.first_half_start
            time = max(tdelta.total_seconds(), 1)
            self.stime = max(time-halftime, 0)
            self.ftime = time - self.stime

        if timeline.second_half_start and self.time >= timeline.second_half_start:
            tdelta = self.time - timeline.second_half_start
            time = max(tdelta.total_seconds(), 1) + halftime
            self.stime = max(time-fulltime, 0)
            self.ftime = time - self.stime

        self.save()

    def save(self, *args, **kwargs):
        halftime = int(MATCHTIME*60/2)  # seconds
        fulltime = int(MATCHTIME*60)  # seconds
        match = self.get_match()
        if self.ftime == -1 and self.stime == -1:
            if not match:
                super().save(*args, **kwargs)
                return
            timeline = getattr(match, 'matchtimeline', None)
            if not timeline:
                super().save(*args, **kwargs)
                return

            if timeline.first_half_start and self.time >= timeline.first_half_start:
                tdelta = self.time - timeline.first_half_start
                time = max(tdelta.total_seconds(), 1)
                self.stime = max(time-halftime, 0)
                self.ftime = time - self.stime

            if timeline.second_half_start and self.time >= timeline.second_half_start:
                tdelta = self.time - timeline.second_half_start
                time = max(tdelta.total_seconds(), 1) + halftime
                self.stime = max(time-fulltime, 0)
                self.ftime = time - self.stime

        super().save(*args, **kwargs)

    def get_event_kind(self):
        if self.event_kind:
            return self.event_kind

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

    def get_event_side(self):
        match = self.get_match()
        club = self.get_club()
        side = 'neutral'
        if match and club:
            side = 'home'
            if match.away == club:
                side = 'away'
        return side

    def get_event_url(self):
        if hasattr(self, 'get_absolute_url'):
            return self.get_absolute_url()
        else:
            return None

    def get_event_time_label(self):
        if self.event_time_label:
            return self.event_time_label
        elif hasattr(self, 'ftime') and hasattr(self, 'stime'):
            return get_time_string(self.ftime, self.stime)
        else:
            return None

    def create_timeline_event(self):
        match = self.get_match()
        if not match:
            raise EventMatchNotAvailable
        timeline, created = MatchTimeLine.objects.get_or_create(match=match)
        return Events.objects.create(matchtimeline=timeline, content_object=self)


class TimeEvents(TimeStampedModel, StatusModel, EventModel):
    event_side = 'neutral'
    STATUS = Choices(('kickoff', 'Kickoff'),
                     ('half_time', 'Half Time'),
                     ('second_half', 'Second Half'),
                     ('final_time', 'Full Time'))

    sublabel = models.CharField(max_length=50, blank=True)
    match = models.ForeignKey(
        Matches, on_delete=models.PROTECT, related_name='timeevents')

    class Meta:
        unique_together = ['match', 'status']

    def get_event_label(self):
        return TimeEvents.STATUS[self.status]

    def get_event_sublabel(self):
        if self.status in [self.STATUS.kickoff, self.STATUS.second_half]:
            return timezone.localtime(self.time).strftime('%I:%M %p')
        return "{} ( {} )".format(self.sublabel, get_time_string(self.ftime, self.stime))


class Squad(StatusModel, TimeStampedModel, EventModel):
    event_kind = 'lineup'
    event_label = 'Line Up'
    KIND = Choices(('parent', 'Parent'),
                   ('first', 'First Team'),
                   ('bench', 'Sub'),
                   ('playing', 'Playing'),
                   ('onbench', 'On bench'),
                   ('tobench', 'To bench'),
                   ('avail', 'Available'),
                   ('suspen', 'Suspended'),
                   )
    STATUS = Choices('pre', 'finalized', 'approved')
    kind = models.CharField(
        max_length=10, choices=KIND, default=KIND.parent)
    match = models.ForeignKey(
        Matches, on_delete=models.PROTECT, null=True, related_name='squad')
    club = models.ForeignKey(
        ClubProfile, on_delete=models.PROTECT, null=True, related_name='squads')
    players = models.ManyToManyField(PlayerProfile, related_name='squads')
    parent = models.ForeignKey(
        'self', on_delete=models.PROTECT, null=True, related_name='items')
    num_players = models.PositiveIntegerField(default=0)
    nU19 = models.PositiveIntegerField(default=0)
    nU21 = models.PositiveIntegerField(default=0)
    NU19S = models.PositiveIntegerField(default=NU19)
    NU21S = models.PositiveIntegerField(default=NU21)

    class Meta:
        unique_together = ['club', 'match']

    class LimitReached(Exception):
        pass

    class NotEnoughPlayers(Exception):
        pass

    class GotSuspension(Exception):
        pass

    def __str__(self):
        if self.parent:
            return '{} ({})'.format(self.parent, self.kind)
        else:
            return '{} squad for {}'.format(self.club.abbr.upper(), self.match)

    def is_nU19(self):
        return self.nU19 >= self.NU19S

    def is_nU21(self):
        return self.nU21 >= self.NU21S

    def is_pre(self):
        return self.status == self.STATUS.pre

    def is_finalized(self):
        return self.status == self.STATUS.finalized

    def is_approved(self):
        return self.status == self.STATUS.approved

    def title(self):
        return self.KIND[self.kind]

    def get_event_time_label(self):
        return ""

    def raise_red_card(self, player):
        if player in self.get_playing_squad().players.all():
            self.get_playing_squad().remove_player(player)
            if player.get_age() <= 19:
                self.NU19S = max(0, self.NU19S-1)
            if player.get_age() <= 21:
                self.NU21S = max(0, self.NU21S-1)
            self.save()
        elif player in self.get_onbench_squad().players.all():
            self.get_onbench_squad().remove_player(player)
        elif player in self.get_tobench_squad().players.all():
            self.get_tobench_squad().remove_player(player)

    def delete_red_card(self, player):
        self.get_playing_squad().add_player(player)
        if player.get_age() <= 19:
            self.NU19S = max(0, self.NU19S+1)
        if player.get_age() <= 21:
            self.NU21S = max(0, self.NU21S+1)
        self.save()

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
    def _create_tobench(cls, parent):
        return cls.objects.create(kind=cls.KIND.tobench, parent=parent)

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
            cls._create_tobench(parent)
            avail = cls._create_avail(parent)
            suspen = cls._create_suspen(parent)
            for player in club.get_players():
                if Suspension.has_suspension(player):
                    suspen.add_player(player)
                else:
                    avail.add_player(player)

        return parent

    def reset(self, hard=False):
        with transaction.atomic():
            for squad in (self.get_avail_squad(),
                          self.get_first_squad(),
                          self.get_playing_squad(),
                          self.get_bench_squad(),
                          self.get_onbench_squad(),
                          self.get_tobench_squad(),
                          self.get_suspen_squad()):
                if squad:
                    squad.players.clear()
                    squad.num_players = 0
                    squad.nU21 = 0
                    squad.nU19 = 0
                    squad.save()

            suspen = self.get_suspen_squad()
            avail = self.get_avail_squad()
            for player in self.club.get_players():
                if Suspension.has_suspension(player):
                    suspen.add_player(player)
                else:
                    avail.add_player(player)

    @ classmethod
    def get_squad(cls, match, club):
        return cls.objects.get(match=match, club=club)

    @ classmethod
    def get_squad_player(cls, match, player):
        club = player.get_club()
        return cls.get_squad(match, club)

    def get_first_squad(self):
        return self.items.filter(kind=self.KIND.first).first()

    def get_bench_squad(self):
        return self.items.filter(kind=self.KIND.bench).first()

    def get_onbench_squad(self):
        return self.items.filter(kind=self.KIND.onbench).first()

    def get_tobench_squad(self):
        return self.items.filter(kind=self.KIND.tobench).first()

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

    def get_tobench_players(self):
        return self.get_tobench_squad().players.all()

    def get_playing_players(self):
        return self.get_playing_squad().players.all()

    def get_suspen_players(self):
        return self.get_suspen_squad().players.all()

    def get_avail_players(self):
        return self.get_avail_squad().players.all()

    def add_player(self, player):
        with transaction.atomic():
            if player not in self.players.all():
                if player.get_age() <= 21 and player.get_age() != 0:
                    self.nU21 += 1
                if player.get_age() <= 19 and player.get_age() != 0:
                    self.nU19 += 1
                self.players.add(player)
                self.num_players += 1
                self.save()

    def remove_player(self, player):
        with transaction.atomic():
            if player in self.players.all():
                if player.get_age() <= 21 and player.get_age() != 0:
                    self.nU21 -= 1
                if player.get_age() <= 19 and player.get_age() != 0:
                    self.nU19 -= 1
                self.players.remove(player)
                self.num_players -= 1
                self.save()

    def add_player_to_playing(self, player):
        if self.get_playing_players().count() >= NFIRST:
            raise self.LimitReached
        if player.get_club() != self.club:
            raise NotMyMatch
        self.get_playing_squad().add_player(player)

    def add_player_to_onbench(self, player):
        if player.get_club() != self.club:
            raise NotMyMatch
        self.get_onbench_squad().add_player(player)

    def add_player_to_tobench(self, player):
        if player.get_club() != self.club:
            raise NotMyMatch
        self.get_tobench_squad().add_player(player)

    def add_player_to_first(self, player):
        with transaction.atomic():
            if player.get_club() != self.club:
                raise NotMyMatch
            if self.get_first_players().count() >= NFIRST:
                raise self.LimitReached
            if Suspension.has_suspension(player):
                raise self.GotSuspension
            if not self.match.is_player_playing(player):
                raise NotMyMatch

            if player in self.get_avail_players():
                self.get_avail_squad().remove_player(player)
                self.get_first_squad().add_player(player)
                self.get_playing_squad().add_player(player)

    def add_player_to_bench(self, player):
        with transaction.atomic():
            if player.get_club() != self.club:
                raise NotMyMatch
            if self.get_bench_players().count() >= NSUB:
                raise self.LimitReached
            if Suspension.has_suspension(player):
                raise self.GotSuspension
            if not self.match.is_player_playing(player):
                raise NotMyMatch
            if player in self.get_avail_players():
                self.get_avail_squad().remove_player(player)
                self.get_bench_squad().add_player(player)
                self.get_onbench_squad().add_player(player)

    def remove_player_from_playing(self, player):
        self.get_playing_squad().remove_player(player)

    def remove_player_from_onbench(self, player):
        self.get_onbench_squad().remove_player(player)

    def remove_player_from_tobench(self, player):
        self.get_tobench_squad().remove_player(player)

    def remove_player_from_first(self, player):
        if player in self.get_first_players():
            self.get_first_squad().remove_player(player)
            self.get_playing_squad().remove_player(player)
            self.get_avail_squad().add_player(player)

    def remove_player_from_bench(self, player):
        if player in self.get_bench_players():
            self.get_bench_squad().remove_player(player)
            self.get_onbench_squad().remove_player(player)
            self.get_avail_squad().add_player(player)

    def get_available_players(self):
        return self.get_avail_players()

    def check_nU(self):
        if not self.get_playing_squad().is_nU19():
            raise self.NotEnoughPlayers('Not enough U19 players')
        if not self.get_playing_squad().is_nU21():
            raise self.NotEnoughPlayers('Not enough U21 players')

    def finalize(self, bypassU=False):
        with transaction.atomic():
            if not bypassU:
                self.check_nU()
            if self.get_playing_squad().num_players < NPLAYERS:
                raise self.NotEnoughPlayers('Not enough players')

            if not self.is_finalized():
                self.create_timeline_event()
            self.status = self.STATUS.finalized
            self.save()

    def substitute(self, playerin, playerout, user,
                   ftime=-1, stime=-1, reason_text=None,
                   bypassU=False):
        with transaction.atomic():
            self.get_playing_squad().add_player(playerin)
            self.get_playing_squad().remove_player(playerout)
            self.get_onbench_squad().remove_player(playerin)
            self.get_tobench_squad().add_player(playerout)
            if not bypassU:
                self.check_nU()
            reason = None
            if reason_text:
                reason, created = SubstitutionReason.objects.get_or_create(
                    text=reason_text)

            obj = Substitution.objects.create(
                squad=self, created_by=user,
                sub_in=playerin, sub_out=playerout,
                reason=reason, ftime=ftime, stime=stime)
            obj.create_timeline_event()
            return obj

    def get_absolute_url(self):
        return reverse('match:squad', kwargs={'pk': self.pk})


class CardReason(NoteModel):
    pass


class Cards(TimeStampedModel, StatusModel, SoftDeletableModel, EventModel):
    STATUS = Choices('active', 'inactive', 'approved')
    COLOR = Choices('red', 'yellow')
    event_sublabel_field = 'reason'
    color = models.CharField(
        max_length=10, choices=COLOR, default=COLOR.yellow)
    match = models.ForeignKey(
        Matches, on_delete=models.PROTECT, related_name='cards')
    player = models.ForeignKey(
        PlayerProfile, on_delete=models.PROTECT, related_name='cards')
    club = models.ForeignKey(
        ClubProfile, on_delete=models.PROTECT, related_name='cards')
    reason = models.ForeignKey(
        CardReason,
        on_delete=models.PROTECT,
        null=True)

    class GotRedAlready(Exception):
        pass

    def get_event_label(self):
        return self.player.__str__().capitalize()

    def get_event_kind(self):
        return self.color

    def save(self, *args, **kwargs):
        self.club = self.player.get_club()
        super().save(*args, **kwargs)

    @ classmethod
    def get_all_reds(cls, match):
        return cls.objects.filter(match=match, color=cls.COLOR.red)

    @ classmethod
    def get_all_yellow(cls, match):
        return cls.objects.filter(match=match, color=cls.COLOR.yellow)

    @ classmethod
    def finalize_match(cls, match):
        # Red cards
        for card in cls.get_all_reds(match):
            reason, created = SuspensionReason.objects.get_or_create(
                text='Red card')
            Suspension.create(card.player, reason)

        # Yellow cards
        for card in cls.get_all_yellow(match):
            player = card.player
            accu, created = AccumulatedCards.objects.get_or_create(
                player=player)
            accu.add_yellow()

    @ classmethod
    def raise_red_card(cls, match, player, reason_text, ftime=-1, stime=-1):
        with transaction.atomic():
            cls.objects.filter(match=match, player=player).update(
                is_removed=True)
            reason, created = CardReason.objects.get_or_create(
                text=reason_text)
            squad = Squad.get_squad_player(match, player)
            squad.raise_red_card(player)
            obj = cls.objects.create(
                match=match, player=player,
                color=cls.COLOR.red, reason=reason,
                ftime=ftime, stime=stime)
            obj.create_timeline_event()

    @ classmethod
    def raise_yellow_card(cls, match, player, reason_text, ftime=-1, stime=-1):
        with transaction.atomic():
            red = cls.objects.filter(
                match=match, player=player, color=cls.COLOR.red).first()
            if red:
                raise cls.GotRedAlready

            yellow1 = cls.objects.filter(
                match=match, player=player, color=cls.COLOR.yellow).first()

            reason, created = CardReason.objects.get_or_create(
                text=reason_text)
            obj = cls.objects.create(
                match=match, player=player,
                color=cls.COLOR.yellow, reason=reason,
                ftime=ftime, stime=stime)

            obj.create_timeline_event()

            if yellow1:
                reason1, created = CardReason.objects.get_or_create(
                    text='second yellow')
                cls.raise_red_card(match, player, reason1,
                                   ftime=ftime, stime=stime)


class SubstitutionReason(NoteModel):
    pass


class Substitution(StatusModel, TimeStampedModel, EventModel):
    STATUS = Choices('submitted', 'finalized', 'approved')
    event_kind = 'sub'
    squad = models.ForeignKey(
        Squad, on_delete=models.PROTECT, related_name='subs')
    club = models.ForeignKey(
        ClubProfile, on_delete=models.PROTECT, related_name='subs')
    match = models.ForeignKey(
        Matches, on_delete=models.PROTECT, related_name='subs')
    sub_in = models.ForeignKey(
        PlayerProfile, on_delete=models.PROTECT, related_name='sub_ins')
    sub_out = models.ForeignKey(
        PlayerProfile, on_delete=models.PROTECT, related_name='sub_outs')
    reason = models.ForeignKey(
        SubstitutionReason,
        on_delete=models.PROTECT,
        null=True)

    def save(self, *args, **kwargs):
        self.match = self.squad.match
        self.club = self.squad.club
        super().save(*args, **kwargs)

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


class Goal(StatusModel, TimeStampedModel, EventModel):
    event_kind = 'goal'
    STATUS = Choices('submitted', 'finalized', 'approved')
    own = models.BooleanField(default=False)
    player = models.ForeignKey(
        PlayerProfile, on_delete=models.SET_NULL, null=True, related_name='goals')
    club = models.ForeignKey(
        ClubProfile, on_delete=models.PROTECT, related_name='goals')
    match = models.ForeignKey(
        Matches, on_delete=models.PROTECT, related_name='goals')
    attr = models.ForeignKey(
        GoalAttr, on_delete=models.PROTECT,
        null=True, related_name='goals')
    time = models.DateTimeField(default=timezone.now)

    def __str__(self):
        if self.own:
            return "Goal(own): {}".format(self.player)
        return "Goal: {}".format(self.player)

    @ classmethod
    def create(cls, match, player, created_by=None,
               ftime=-1, stime=-1, own=False, attr=None):
        goalattr = None
        if attr:
            goalattr, created = GoalAttr.objects.get_or_create(text=attr)

        obj = cls.objects.create(
            match=match,
            player=player,
            created_by=created_by,
            ftime=ftime,
            stime=stime,
            own=own,
            attr=goalattr)
        obj.create_timeline_event()
        return obj

    def remove(self):
        with transaction.atomic():
            self.timeline_event.all().delete()
            self.delete()

    def get_event_label(self):
        if self.own:
            return "goal (own)".format(self.player)
        return "goal: <strong>{}</strong>".format(self.player)

    def get_event_sublabel(self):
        if self.own:
            return self.player
        return self.attr

    def save(self, *args, **kwargs):
        if self.own:
            self.club = self.match.get_opponent_club_of_player(self.player)
        else:
            self.club = self.player.get_club()
        super().save(*args, **kwargs)

    @ classmethod
    def score(cls, match):
        return (cls.objects.filter(match=match, club=match.home).count(),
                cls.objects.filter(match=match, club=match.away).count(),)

    @ classmethod
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

    @ classmethod
    def has_suspension(cls, player):
        return cls.pending.filter(player=player).exists()

    @ classmethod
    def create(cls, player, reason):
        return cls.pending.create(player=player, reason=reason)

    @ classmethod
    def set_completed(cls, player):
        susp = cls.pending.filter(player).first()
        if susp:
            susp.status = cls.STATUS.completed
            susp.save()

    @ classmethod
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
            reason, created = SuspensionReason.objects.get_or_create(
                text='Yellow card ban')
            Suspension.create(player, reason)
            self.yellow = 0
        self.save()
