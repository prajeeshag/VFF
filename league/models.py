from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone


class League(models.Model):
    long_name = models.CharField(
        _('Long name'), max_length=200)
    short_name = models.CharField(_('Short name'), max_length=50, blank=True)
    abbr = models.CharField(_('Abbreviation'), max_length=10)

    def __str__(self):
        return self.long_name


class Season(models.Model):
    league = models.ForeignKey(League, on_delete=models.PROTECT)
    name = models.CharField(_('Season'), max_length=32)
    cro_datetime = models.DateTimeField(
        _('Club Registration Opening Date'), default=timezone.now)
    crc_datetime = models.DateTimeField(
        _('Club Registration Closing Date'), default=timezone.now)
    twc_datetime = models.DateTimeField(
        _('Transfer Window closing date'), default=timezone.now)

    def is_transfer_window_open(self):
        now = timezone.now()
        return self.twc_datetime > now

    def __str__(self):
        return "{} {}".format(self.league.abbr, self.name)
