
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils.crypto import get_random_string
from users.models import PlayerProfile
from ...models import Verification


class Command(BaseCommand):
    help = 'Create Verification'

    def handle(self, *args, **kwargs):
        for player in PlayerProfile.objects.all():
            Verification.objects.create(profile=player)
