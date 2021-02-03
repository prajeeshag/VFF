from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils.crypto import get_random_string

from ...models import League, Season


class Command(BaseCommand):
    help = 'Create VFL2021'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **kwargs):
        league, created = League.objects.get_or_create(
            long_name='Vaniyamkulam Football League',
            short_name='vleague',
            abbr='VFL'
        )

        Season.objects.get_or_create(
            league=league,
            name='2021'
        )
