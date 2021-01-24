from django.db import models
from django.core.validators import MinValueValidator

from django.utils.translation import ugettext_lazy as _

from users.models import ClubProfile as Club, Grounds

LEAGUE_NAME = 'VFL'


class Fixture(models.Model):
    season = models.CharField(_('Season'), unique=True, max_length=20)

    def __str__(self):
        return "{} {}".format(LEAGUE_NAME, self.season)


class Matches(models.Model):
    num = models.PositiveIntegerField(
        _('Match Number'), validators=[MinValueValidator(1), ],
        default=1)
    home = models.ForeignKey(
        Club, on_delete=models.PROTECT, related_name='home_matches')
    away = models.ForeignKey(
        Club, on_delete=models.PROTECT, related_name='away_matches')
    date = models.DateTimeField(_('Date'))
    ground = models.ForeignKey(
        Grounds, on_delete=models.PROTECT, null=True, related_name='matches')
    fixture = models.ForeignKey(
        Fixture, on_delete=models.PROTECT, null=True, related_name='matches')

    class Meta:
        unique_together = ['fixture', 'home', 'away', 'num']
        ordering = ['date']

    def __str__(self):
        return "{} x {}".format(self.home, self.away)
