from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils.crypto import get_random_string

from match.models import *
from fixture.models import Matches


class Command(BaseCommand):
    help = 'Set against field and create result'

    def handle(self, *args, **kwargs):
        for cls in [Goal, Cards, Substitution]:
            for obj in cls.objects.all():
                obj.save()

        for m in Matches.objects.all():
            Result.create(m)
