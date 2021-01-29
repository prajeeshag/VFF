from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils.crypto import get_random_string
from ... import models


class Command(BaseCommand):
    help = 'Activate Player Profile permissions'

    def handle(self, *args, **kwargs):
        for profile in models.PlayerProfile.objects.all():
            profile.save()
