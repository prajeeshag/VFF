from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils.crypto import get_random_string

import pickle
import datetime
import pytz

from fixture.models import Fixture, Matches
from users.models import ClubProfile as Club


class Command(BaseCommand):
    help = 'Populate email field with random email address for existing users'

    def add_arguments(self, parser):
        parser.add_argument('--file', action='store', default='fixture.dat',
                            type=str, help='Fixture file')
        parser.add_argument('--reset', action='store_true',
                            help='Reset all matches in Fixture')

    def handle(self, *args, **kwargs):
        ffile = kwargs['file']
        reset = kwargs['reset']
        with open(ffile, "rb") as fb:
            dat = pickle.load(fb)
        fixture = Fixture.objects.first()
        if not fixture:
            fixture = Fixture.objects.create(season='2021')
        for it in dat:
            date = it['date']
            away = Club.objects.get(pk=it['away'])
            home = Club.objects.get(pk=it['home'])
            ground = home.home_ground
            try:
                obj = Matches.objects.get(home=home, away=away)
            except Matches.DoesNotExist:
                obj = Matches.objects.create(
                    home=home, away=away, ground=ground,
                    date=date, fixture=fixture
                )
                print(obj)
                continue

            if not obj.is_fixed() and not obj.is_done():
                obj.delete()
                obj = Matches.objects.create(
                    home=home, away=away, ground=ground,
                    date=date, fixture=fixture
                )
                print(obj)
