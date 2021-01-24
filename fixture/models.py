from django.db import models

from django.utils.translation import ugettext_lazy as _

from users.models import ClubProfile as Club


class Fixture(models.Model):
    season = models.PositiveIntegerField(_('Season'), unique=True)


class Matches(models.Model):
    home = models.ForeignKey(
        Club, on_delete=models.CASCADE, related_name='home_matches')
    away = models.ForeignKey(
        Club, on_delete=models.CASCADE, related_name='away_matches')
    date = models.DateTimeField(_('Date'))
