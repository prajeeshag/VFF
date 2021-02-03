from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils.crypto import get_random_string
from ... import models


class Command(BaseCommand):
    help = 'Activate Player Profile permissions'

    def handle(self, *args, **kwargs):
        for profile in models.Document.objects.all():
            print('pk=', profile.pk)
            profile.save(set_orientation=True)
