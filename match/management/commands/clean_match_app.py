from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils.crypto import get_random_string

from match.models import *


class Command(BaseCommand):
    help = 'match app cleanup'

    def handle(self, *args, **kwargs):
        Goal.objects.all().delete()
        TimeEvents.objects.all().delete()
        Cards.objects.all().delete()
        Events.objects.all().delete()
        MatchTimeLine.objects.all().delete()
        Substitution.objects.all().delete()
        while Squad.objects.last():
            Squad.objects.last().delete()
