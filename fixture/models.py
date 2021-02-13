import datetime as dt

from django.utils import timezone
from django.db import models
from django.db.models import Q
from django.core.validators import MinValueValidator
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import Group

from model_utils.models import StatusModel, TimeStampedModel
from model_utils import Choices

from users.models import ClubProfile, Grounds

LEAGUE_NAME = 'VFL'


class Fixture(models.Model):
    season = models.CharField(_('Season'), unique=True, max_length=20)

    def __str__(self):
        return "{} {}".format(LEAGUE_NAME, self.season)


class Matches(TimeStampedModel, StatusModel):
    STATUS = Choices('done', 'fixed', 'tentative', 'canceled', 'postponed')

    num = models.PositiveIntegerField(
        _('Match Number'), validators=[MinValueValidator(1), ],
        default=1)
    home = models.ForeignKey(
        ClubProfile, on_delete=models.PROTECT, related_name='home_matches')
    away = models.ForeignKey(
        ClubProfile, on_delete=models.PROTECT, related_name='away_matches')
    date = models.DateTimeField(_('Date'))
    ground = models.ForeignKey(
        Grounds, on_delete=models.PROTECT, null=True, related_name='matches')
    fixture = models.ForeignKey(
        Fixture, on_delete=models.PROTECT, null=True, related_name='matches')
    status = models.CharField(
        max_length=20, choices=STATUS, default=STATUS.tentative)
    note = models.CharField(max_length=200, blank=True)

    class Meta:
        unique_together = ['fixture', 'home', 'away', 'num']
        ordering = ['date']

    def __str__(self):
        return "{} x {}".format(self.home.abbr.upper(), self.away.abbr.upper())

    def get_home_squad(self):
        if hasattr(self, 'squad'):
            return self.squad.filter(club=self.home).first()
        return None

    def get_away_squad(self):
        if hasattr(self, 'squad'):
            return self.squad.filter(club=self.away).first()
        return None

    def is_playing(self, club):
        if club == self.home or club == self.away:
            return True
        return False

    def is_player_playing(self, player):
        club = player.get_club()
        return self.is_playing(club)

    def get_opponent_club(self, club):
        if club == self.away:
            return self.home
        elif club == self.home:
            return self.away
        return None

    def score_string(self):
        return "{} - {}".format(self.num_home_goals(), self.num_away_goals())

    def get_opponent_club_of_player(self, player):
        return self.get_opponent_club(player.get_club())

    def get_day_nY(self):
        return self.date.strftime("%b. %d %a")

    def get_time(self):
        return self.date.strftime('%H:%M %p')

    @classmethod
    def get_tentative_matches(cls):
        return cls.tentative.all()

    @classmethod
    def get_done_matches(cls):
        return cls.done.all()

    @classmethod
    def get_fixed_matches(cls):
        return cls.fixed.all()

    @classmethod
    def get_past_matches(cls):
        date = timezone.now()
        return cls.objects.filter(date__lt=date)

    @classmethod
    def get_upcoming_matches(cls):
        date = timezone.now()
        return cls.objects.filter(date__gte=date)

    @classmethod
    def get_matches_of_club(cls, club):
        return cls.objects.filter(Q(home=club) | Q(away=club))

    @classmethod
    def get_home_matches_of_club(cls, club):
        return cls.objects.filter(Q(home=club))

    @classmethod
    def get_past_matches_of_club(cls, club):
        date = timezone.now()
        return cls.get_matches_of_club(club).filter(date__lt=date)

    @classmethod
    def get_done_matches_of_club(cls, club):
        return cls.get_matches_of_club(club).filter(status=self.STATUS.done)

    @classmethod
    def get_upcoming_matches_of_club(cls, club):
        date = timezone.now()
        return cls.get_matches_of_club(club).filter(date__gte=date)

    @classmethod
    def get_next_match_of_club(cls, club):
        return cls.get_upcoming_matches_of_club(club).first()

    @classmethod
    def get_prev_match_of_club(cls, club):
        return cls.get_past_matches_of_club(club).last()

    @ classmethod
    def get_upcoming_home_matches_of_club(cls, club):
        date = timezone.now()
        return cls.get_home_matches_of_club(club).filter(date__gte=date)

    @classmethod
    def get_current_next_match_of_club(cls, club):
        """ Get next including ongoing match """
        prev_match = cls.get_prev_match_of_club(club)
        if prev_match.is_done():
            return cls.get_next_match_of_club(club)
        else:
            return prev_match

    def set_done(self):
        self.status = self.STATUS.done
        self.save()


def add_is_status(status):
    fn_name = 'is_' + status

    def fn(self):
        return self.status == getattr(self.STATUS, status)
    setattr(Matches, fn_name, fn)
    fn.__name__ = fn_name
    fn.__doc__ = "Returns True if status is {}".format(status)


for stat in Matches.STATUS:
    add_is_status(stat[0])


def num_played(self, against):
    if against:
        return Matches.objects.filter(
            Q(home=self) | Q(away=self),
            Q(home__in=against) | Q(away__in=against),
            status=Matches.STATUS.done)
    else:
        return Matches.objects.filter(
            Q(home=self) | Q(away=self),
            status=Matches.STATUS.done)


setattr(ClubProfile, 'num_played', num_played)
