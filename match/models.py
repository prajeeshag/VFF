import humanize
import math
from itertools import chain

from django.db import models, transaction
from django.db.models import Count
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
            if not time:
                time = timezone.now()

            self.save()

            obj = TimeEvents.objects.create(match=self.match,
                                            time=time,
                                            status=TimeEvents.STATUS.kickoff)
            Events.objects.create(
                matchtimeline=self,
                content_object=obj,)


    def start_second_half(self, time=None):
        with transaction.atomic():
            if not time:
                time = timezone.now()
            self.save()
            obj = TimeEvents.objects.create(match=self.match,
                                            time=time,
                                            status=TimeEvents.STATUS.second_half)
            Events.objects.create(
                matchtimeline=self,
                content_object=obj,)

    def set_half_time(self, time=None):
        with transaction.atomic():
            if not time:
                time = timezone.now()
            score = Goal.score_as_string(self.match)
            obj = TimeEvents.objects.create(
                match=self.match, status=TimeEvents.STATUS.half_time,
                time=time, sublabel=score)
            Events.objects.create(
                matchtimeline=self,
                content_object=obj,)

    def set_final_time(self, time=None):
        with transaction.atomic():
            if not time:
                time = timezone.now()

            score = Goal.score_as_string(self.match)
            obj = TimeEvents.objects.create(
                match=self.match,
                status=TimeEvents.STATUS.final_time,
                time=time, sublabel=score)
            Events.objects.create(
                matchtimeline=self,
                content_object=obj,)


class Events(TimeStampedModel):
    matchtimeline = models.ForeignKey(MatchTimeLine, on_delete=models.PROTECT)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    ftime = models.IntegerField(default=-1)
    stime = models.IntegerField(default=-1)

    class Meta:
        ordering = ['-ftime', '-stime', '-pk']

    def __str__(self):
        return self.label()

    def kind(self):
        if self.content_object:
            return self.content_object.get_event_kind()

    def side(self):
        if self.content_object:
            return self.content_object.get_event_side()

    def label(self):
        if self.content_object:
            return self.content_object.get_event_label()

    def sublabel(self):
        if self.content_object:
            return self.content_object.get_event_sublabel()

    def url(self):
        if self.content_object:
            return self.content_object.get_event_url()

    def time_label(self):
        if self.content_object:
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

        first_half_start = match.kickoff()
        if first_half_start and self.time >= first_half_start:
            tdelta = self.time - first_half_start
            time = max(tdelta.total_seconds(), 1)
            self.stime = max(time-halftime, 0)
            self.ftime = time - self.stime

        second_half_start = match.second_half()
        if second_half_start and self.time >= second_half_start:
            tdelta = self.time - second_half_start
            time = max(tdelta.total_seconds(), 1) + halftime
            self.stime = max(time-fulltime, 0)
            self.ftime = time - self.stime

        self.save()
        for ev in self.timeline_event.all():
            ev.save()

    def save(self, *args, **kwargs):
        halftime = int(MATCHTIME*60/2)  # seconds
        fulltime = int(MATCHTIME*60)  # seconds
        match = self.get_match()
        if not match:
            super().save(*args, **kwargs)
            return

        # set against
        if hasattr(self, 'club') and self.club:
            self.against = match.get_opponent_club(self.club)

        # Calculate match time
        if self.ftime == -1 and self.stime == -1:

            first_half_start = match.kickoff()
            if first_half_start and self.time >= first_half_start:
                tdelta = self.time - first_half_start
                time = max(tdelta.total_seconds(), 1)
                self.stime = max(time-halftime, 0)
                self.ftime = time - self.stime

            second_half_start = match.second_half()
            if second_half_start and self.time >= second_half_start:
                tdelta = self.time - second_half_start
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

    def get_edit_url(self):
        return reverse('match:edittimeevent', args=[self.pk])


class Squad(StatusModel, TimeStampedModel, EventModel):
    event_kind = 'lineup'
    event_label = 'Line Up'
    KIND = Choices(('parent', 'Parent'),
                   ('first', 'First Team'),
                   ('bench', 'Sub'),
                   ('playing', 'Playing'),
                   ('onbench', 'On bench'),
                   ('played', 'Played'),
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
    against = models.ForeignKey(
        ClubProfile, on_delete=models.PROTECT,
        null=True, related_name='squads_against')
    players = models.ManyToManyField(PlayerProfile, related_name='squads')
    parent = models.ForeignKey(
        'self', on_delete=models.PROTECT, null=True, related_name='items')
    num_players = models.PositiveIntegerField(default=0)
    nU19 = models.PositiveIntegerField(default=0)
    nU21 = models.PositiveIntegerField(default=0)
    NU19S = models.PositiveIntegerField(default=NU19)
    NU21S = models.PositiveIntegerField(default=NU21)

    class Meta:
        unique_together = ['club', 'match', 'kind']

    class LimitReached(Exception):
        pass

    class NotEnoughPlayers(Exception):
        pass

    class GotSuspension(Exception):
        pass

    class PlayerNotInSquad(Exception):
        pass

    def __str__(self):
        if self.parent:
            return '{} ({})'.format(self.parent, self.kind)
        else:
            return '{} squad for {}'.format(self.club.abbr.upper(), self.match)

    def get_edit_url(self):
        return reverse('dash:addfirstteam', args=[self.match.pk,self.club.pk])

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
    def create(cls, match, club, user):
        parent = None
        with transaction.atomic():
            parent = cls._create_parent(
                created_by=user, club=club, match=match)
            for kind in cls.KIND:
                if kind[0] != cls.KIND.parent:
                    cls.objects.create(kind=kind[0], parent=parent,
                                       club=club, match=match,
                                       created_by=user,
                                       status=cls.STATUS.pre)
            avail = parent.get_avail_squad()
            suspen = parent.get_suspen_squad()
            for player in club.get_players():
                if Suspension.has_suspension(player):
                    suspen.add_player(player)
                else:
                    avail.add_player(player)
        return parent

    def reset(self):
        with transaction.atomic():
            for squad in (self.get_avail_squad(),
                          self.get_first_squad(),
                          self.get_playing_squad(),
                          self.get_bench_squad(),
                          self.get_onbench_squad(),
                          self.get_played_squad(),
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
                if not player.verification.is_verified():
                    continue
                if Suspension.has_suspension(player):
                    suspen.add_player(player)
                else:
                    avail.add_player(player)

    @ classmethod
    def get_squad(cls, match, club):
        return cls.objects.get(match=match, club=club, kind=cls.KIND.parent)

    @ classmethod
    def get_squad_player(cls, match, player):
        club = player.get_club()
        return cls.get_squad(match, club)

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
                self.num_players -= 1
                self.players.remove(player)
                self.save()
                return True
            else:
                return False

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

    def add_player_to_played(self, player):
        if player.get_club() != self.club:
            raise NotMyMatch
        self.get_played_squad().add_player(player)

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
                self.get_played_squad().add_player(player)

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

    def remove_player_from_played(self, player):
        self.get_played_squad().remove_player(player)

    def remove_player_from_first(self, player):
        if player in self.get_first_players():
            self.get_first_squad().remove_player(player)
            self.get_playing_squad().remove_player(player)
            self.get_played_squad().remove_player(player)
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

            if not self.is_finalized():
                self.create_timeline_event()
            self.status = self.STATUS.finalized
            self.save()

    def substitute(self, playerin, playerout, user,
                   reason_text=None, time=None):
        with transaction.atomic():
            reason = None
            if reason_text:
                reason, created = SubstitutionReason.objects.get_or_create(
                    text=reason_text)
            if not time:
                time = timezone.now()
            obj = Substitution.objects.create(
                squad=self, created_by=user,
                sub_in=playerin, sub_out=playerout,
                reason=reason, time=time)
            obj.create_timeline_event()
            return obj

    def get_absolute_url(self):
        return reverse('match:squad', kwargs={'pk': self.pk})


def add_get_child_squad(child):
    fn_name = '_'.join(['get', child, 'squad'])

    def fn(self):
        return self.items.filter(kind=child).prefetch_related('players').first()
    setattr(Squad, fn_name, fn)


def add_get_child_players(child):
    fn_name = '_'.join(['get', child, 'players'])

    def fn(self):
        attr_name = '_'.join(['get', child, 'squad'])
        return getattr(self, attr_name)().players.all()
    setattr(Squad, fn_name, fn)

def add_get_child_players_exclude(child):
    fn_name = '_'.join(['get', child, 'players_exclude'])

    def fn(self):
        attr_name = '_'.join(['get', child, 'squad'])
        sqd = getattr(self, attr_name)()
        match = sqd.match
        banned_players = Cards.objects.filter(
            color=Cards.COLOR.red, match=match).values('player')
        return sqd.players.exclude(pk__in=banned_players)
    setattr(Squad, fn_name, fn)


for child in Squad.KIND:
    add_get_child_squad(child[0])
    add_get_child_players(child[0])
    add_get_child_players_exclude(child[0])


def add_is_kind(kind):
    fn_name = 'is_' + kind

    def fn(self):
        return self.kind == getattr(self.KIND, kind)
    setattr(Squad, fn_name, fn)
    fn.__name__ = fn_name
    fn.__doc__ = "Returns True if kind is {}".format(kind)


for kind in Squad.KIND:
    add_is_kind(kind[0])


class SuspensionReason(NoteModel):
    pass


class Suspension(StatusModel, TimeStampedModel):
    STATUS = Choices('pending', 'completed', 'canceled')
    player = models.ForeignKey(PlayerProfile, on_delete=models.PROTECT)
    reason = models.ForeignKey(SuspensionReason, on_delete=models.PROTECT)
    got_in = models.ForeignKey(Matches, on_delete=models.PROTECT, blank=True,
                               null=True, related_name='suspensions')
    completed_in = models.ForeignKey(Matches, on_delete=models.PROTECT, blank=True,
                                     null=True, related_name='suspensions_completed')

    class SuspensionExist(Exception):
        pass

    def __str__(self):
        return 'Suspension - {}'.format(self.player)

    @ classmethod
    def has_suspension(cls, player):
        return cls.pending.filter(player=player).exists()

    @ classmethod
    def create(cls, player, reason, match=None):
        return cls.objects.create(player=player, reason=reason,
                                  status=cls.STATUS.pending, got_in=match)

    @ classmethod
    def set_completed(cls, player, match):
        if cls.completed.filter(player=player, completed_in=match).exists():
            # Only one suspension is completed in one match for a player
            return
        susp = cls.pending.filter(player=player).first()
        if susp:
            susp.status = cls.STATUS.completed
            susp.completed_in = match
            susp.save()

    @ classmethod
    def set_completed_for_match(cls, match):
        with transaction.atomic():
            for club in [match.home, match.away]:
                sqd = Squad.get_squad(match, club).get_suspen_squad()
                players = sqd.players.all()
                for player in players:
                    cls.set_completed(player, match)


class CardReason(NoteModel):
    pass


class Cards(TimeStampedModel, StatusModel, EventModel):
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
        ClubProfile, on_delete=models.PROTECT,
        null=True, related_name='cards')
    against = models.ForeignKey(
        ClubProfile, on_delete=models.PROTECT,
        null=True, related_name='cards_against')
    reason = models.ForeignKey(
        CardReason,
        on_delete=models.PROTECT,
        null=True)
    is_removed = models.BooleanField(default=False)
    suspension = models.ForeignKey(
        Suspension, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='cards')
    red = models.ForeignKey(
        'self', on_delete=models.SET_NULL,
        null=True, related_name='yellows')

    class GotRedAlready(Exception):
        pass

    def __str__(self):
        return '{} card - {}'.format(self.color, self.player)

    def get_edit_url(self):
        return reverse('match:editcard', args=[self.pk])

    def get_event_label(self):
        return self.player.__str__().capitalize()

    def get_event_kind(self):
        return self.color

    def save(self, *args, **kwargs):
        if not self.club:
            self.club = self.player.get_club()
        super().save(*args, **kwargs)

    @ classmethod
    def finalize_match(cls, match):
        with transaction.atomic():
            # Red cards
            for card in cls.objects.filter(match=match,
                                           color=cls.COLOR.red,
                                           suspension=None):
                reason, created = SuspensionReason.objects.get_or_create(
                    text='Red card')
                sus = Suspension.create(card.player, reason, match=match)
                card.suspension = sus
                card.save()

            # Yellow cards
            for mcard in cls.objects.filter(match=match, color=cls.COLOR.yellow, red=None):
                cards = cls.objects.filter(color=Cards.COLOR.yellow,
                                           red=None,
                                           suspension=None,
                                           player=mcard.player)
                if cards.count() > 2:
                    reason, created = SuspensionReason.objects.get_or_create(
                        text='Yellow card ban')
                    sus = Suspension.create(mcard.player, reason, match=match)
                    cards.update(suspension=sus)

    @ classmethod
    def update_suspension(cls):
        with transaction.atomic():
            players = cls.objects.filter(
                color=Cards.COLOR.yellow,
                red=None,
                suspension=None).values(
                'player').annotate(num=Count('player')).filter(num__gt=2)

            for i in players:
                player = PlayerProfile.objects.get(pk=i['player'])
                reason, created = SuspensionReason.objects.get_or_create(
                    text='Yellow card ban')
                sus = Suspension.create(player, reason)
                cls.objects.filter(
                    color=Cards.COLOR.yellow,
                    red=None,
                    suspension=None,
                    player=player).update(suspension=sus)

    @ classmethod
    def raise_red_card(cls, match, player, reason_text, time=None):

        with transaction.atomic():
            yellows = cls.objects.filter(match=match, player=player, color=cls.COLOR.yellow)
            squad = Squad.get_squad_player(match, player)
            reason, created = CardReason.objects.get_or_create(
                text=reason_text)
            if not time:
                time = timezone.now()
            obj = cls.objects.create(
                match=match, player=player,
                color=cls.COLOR.red, reason=reason,
                time=time)
            yellows.update(red=obj)
            obj.create_timeline_event()

    @ classmethod
    def raise_yellow_card(cls, match, player, reason_text, time=None):
        with transaction.atomic():
            red = cls.objects.filter(
                match=match, player=player, color=cls.COLOR.red).first()
            if red:
                raise cls.GotRedAlready

            yellow1 = cls.objects.filter(
                match=match, player=player, color=cls.COLOR.yellow).first()

            reason, created = CardReason.objects.get_or_create(
                text=reason_text)

            if not time:
                time = timezone.now()

            obj = cls.objects.create(
                match=match, player=player,
                color=cls.COLOR.yellow, reason=reason,
                time=time)

            obj.create_timeline_event()

            if yellow1:
                reason1, created = CardReason.objects.get_or_create(
                    text='second yellow')
                cls.raise_red_card(match, player, reason1, time=time)


class SubstitutionReason(NoteModel):
    pass


class Substitution(StatusModel, TimeStampedModel, EventModel):
    STATUS = Choices('submitted', 'finalized', 'approved')
    event_kind = 'sub'
    squad = models.ForeignKey(
        Squad, on_delete=models.PROTECT, related_name='subs')
    club = models.ForeignKey(
        ClubProfile, on_delete=models.PROTECT, related_name='subs')
    against = models.ForeignKey(
        ClubProfile, on_delete=models.PROTECT,
        null=True, related_name='subs_against')
    match = models.ForeignKey(
        Matches, on_delete=models.PROTECT, related_name='subs')
    sub_in = models.ForeignKey(
        PlayerProfile, on_delete=models.PROTECT, related_name='sub_ins')
    sub_out = models.ForeignKey(
        PlayerProfile, on_delete=models.PROTECT,
        related_name='sub_outs')
    reason = models.ForeignKey(
        SubstitutionReason,
        on_delete=models.PROTECT,
        null=True, blank=True)

    def __str__(self):
        return 'In({})-Out({})'.format(self.sub_in,self.sub_out)

    def save(self, *args, **kwargs):
        self.match = self.squad.match
        self.club = self.squad.club
        super().save(*args, **kwargs)

    def get_edit_url(self):
        return reverse('match:editsub', args=[self.pk])

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
        PlayerProfile, on_delete=models.PROTECT,
        null=True, related_name='goals')
    club = models.ForeignKey(
        ClubProfile, on_delete=models.PROTECT, related_name='goals')
    against = models.ForeignKey(
        ClubProfile, on_delete=models.PROTECT,
        null=True, related_name='goals_against')
    match = models.ForeignKey(
        Matches, on_delete=models.PROTECT, related_name='goals')
    attr = models.ForeignKey(
        GoalAttr, on_delete=models.PROTECT,
        null=True, related_name='goals', blank=True)
    time = models.DateTimeField(default=timezone.now)

    def __str__(self):
        if self.own:
            return "Goal(own): {}".format(self.player)
        return "Goal: {}".format(self.player)

    def get_edit_url(self):
        return reverse('match:editgoal', args=[self.pk])

    @ classmethod
    def create(cls, match, player, created_by=None,
               own=False, attr=None, time=None, club_in=None):

        goalattr = None

        if attr:
            goalattr, created = GoalAttr.objects.get_or_create(text=attr)

        if not time:
            time = timezone.now()

        if club_in:
            club = club_in
        else:
            if own:
                club = match.get_opponent_club_of_player(player)
            else:
                club = player.get_club()

        obj = cls.objects.create(
            match=match,
            player=player,
            created_by=created_by,
            own=own,
            attr=goalattr,
            time=time,
            club=club)

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
        self.against = self.match.get_opponent_club(self.club)
        super().save(*args, **kwargs)

    @ classmethod
    def score(cls, match):
        return (cls.objects.filter(match=match, club=match.home).count(),
                cls.objects.filter(match=match, club=match.away).count(),)

    @ classmethod
    def score_as_string(cls, match):
        home, away = cls.score(match)
        return "{} - {}".format(home, away)


class Result(StatusModel):
    STATUS = Choices('not_done', 'result', 'draw')
    winner = models.ForeignKey(
        ClubProfile,
        on_delete=models.PROTECT,
        null=True,
        related_name='wins')
    loser = models.ForeignKey(
        ClubProfile,
        on_delete=models.PROTECT,
        null=True,
        related_name='losses')
    draws = models.ManyToManyField(
        ClubProfile,
        related_name='draws')
    match = models.OneToOneField(Matches,
                                 on_delete=models.PROTECT,
                                 related_name='result')

    @classmethod
    def create(cls, match):
        obj, created = cls.objects.get_or_create(match=match)
        obj.update()
        return obj

    def update(self):
        if not self.match.is_done():
            self.status = self.STATUS.not_done
            self.save()
            return

        score = Goal.score(self.match)
        if score[0] > score[1]:
            self.status = self.STATUS.result
            self.winner = self.match.home
            self.loser = self.match.away
            self.draws.clear()
            self.save()
        elif score[0] < score[1]:
            self.status = self.STATUS.result
            self.winner = self.match.away
            self.loser = self.match.home
            self.draws.clear()
            self.save()
        else:
            self.status = self.STATUS.draw
            self.winner = None
            self.loser = None
            self.save()
            self.draws.add(self.match.away, self.match.home)


# Adding methods
SIDES = ('home', 'away')
EVENTS = {'goals': Goal,
          'cards': Cards,
          'subs': Substitution}


def add_num_side_event(side, eventname, eventcls):
    """ Add num of events method in a match for a side
        for class: Matches
    """
    fn_name = "_".join(['num', side, eventname])

    def fn(self):
        club = getattr(self, side)
        return eventcls.objects.filter(club=club, match=self).count()

    setattr(Matches, fn_name, fn)
    fn.__name__ = fn_name
    fn.__doc__ = "Get # of {} for {} side in Match".format(eventname, side)


def add_num_club_event(eventname, eventcls):
    """ Add num_{event} method
        for class: ClubProfile
    """
    fn_name = "_".join(['num', eventname])

    def fn(self, against=None):
        if against:
            return eventcls.objects.filter(club=self, against__in=against).count()
        else:
            return eventcls.objects.filter(club=self).count()

    setattr(ClubProfile, fn_name, fn)
    fn.__name__ = fn_name
    fn.__doc__ = "Get # of {}".format(eventname)


def add_num_club_event_against(eventname, eventcls):
    """ Add num_{event} method
        for class: ClubProfile
    """
    fn_name = "_".join(['num', eventname, 'against'])

    def fn(self, against=None):
        if against:
            return eventcls.objects.filter(against=self, club__in=against).count()
        else:
            return eventcls.objects.filter(against=self).count()

    setattr(ClubProfile, fn_name, fn)
    fn.__name__ = fn_name
    fn.__doc__ = "Get # of {} against".format(eventname)


for evname, evclass in EVENTS.items():
    add_num_club_event(evname, evclass)
    add_num_club_event_against(evname, evclass)
    for side in SIDES:
        add_num_side_event(side, evname, evclass)


def num_wins(self, against=None):
    if against:
        return Result.objects.filter(winner=self, loser__in=against).count()
    else:
        return Result.objects.filter(winner=self).count()


setattr(ClubProfile, 'num_wins', num_wins)


def num_losses(self, against=None):
    if against:
        return Result.objects.filter(loser=self, winner__in=against).count()
    else:
        return Result.objects.filter(loser=self).count()


setattr(ClubProfile, 'num_losses', num_losses)


def add_num_player_event(eventname, eventcls):
    """ Add num_{event} method
        for class: PlayerProfile
    """
    fn_name = "_".join(['num', eventname])

    def fn(self, against=None):
        if against:
            return eventcls.objects.filter(player=self, against__in=against).count()
        else:
            return eventcls.objects.filter(player=self).count()

    setattr(PlayerProfile, fn_name, fn)
    fn.__name__ = fn_name
    fn.__doc__ = "Get # of {}".format(eventname)


for evname, evclass in EVENTS.items():
    add_num_player_event(evname, evclass)


def get_match_players(self, club=None):
    """
    get all players who played a match including sub
    """
    players = PlayerProfile.objects.none()
    for clb in (self.home, self.away):
        if club:
            if clb != club:
                continue
        sqd = Squad.get_squad(match=self, club=clb)
        p1 = sqd.get_first_players()
        p2 = sqd.get_bench_players()
        players = (players | p1 | p2)
    return players.distinct()


setattr(Matches, 'get_match_players', get_match_players)


def finalize_match(self):
    if self.is_done():
        return
    with transaction.atomic():
        # set suspension completed (if any) for players who was not in squad
        Suspension.set_completed_for_match(self)
        # Finalize Cards
        Cards.finalize_match(self)
        self.set_done()
        # Result
        Result.create(match=self)


setattr(Matches, 'finalize_match', finalize_match)


def add_get_timeevents_time(status):
    """ Add {timeevent} method
        for class: Matches
    """
    fn_name = status

    def fn(self):
        stat = getattr(TimeEvents.STATUS, status)
        try:
            obj = TimeEvents.objects.get(match=self,status=stat)
        except TimeEvents.DoesNotExist:
            return None
        return obj.time

    setattr(Matches, fn_name, fn)
    fn.__name__ = fn_name
    fn.__doc__ = "Get {} time".format(status)


for stat in TimeEvents.STATUS:
    add_get_timeevents_time(stat[0])

