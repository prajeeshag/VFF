from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils.crypto import get_random_string

import pickle
import datetime
import pytz

from fixture.models import Fixture, Matches


class Command(BaseCommand):
    help = 'Match Status correction'

    def handle(self, *args, **kwargs):
        for match in Matches.objects.all():
            match.status = match.status.lower()
            match.save()
