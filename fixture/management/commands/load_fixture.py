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
        print(fixture)
        if reset:
            fixture.matches.all().delete()

        num = 1
        tz = pytz.timezone("Asia/Calcutta")
        for it in dat:
            date = tz.localize(it['date'])
            away = Club.objects.get(pk=it['away'])
            home = Club.objects.get(pk=it['home'])
            ground = home.home_ground
            print(away, home, ground)
            break
            obj = Matches.objects.update_or_create(
                num=num, home=home,
                away=away, date=date,
                ground=ground, fixture=fixture)
            print(obj)
