from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils.crypto import get_random_string


class Command(BaseCommand):
    help = 'Remove Anonymous user'

    def handle(self, *args, **kwargs):
        # Create playercount
        get_user_model().objects.get(username='AnonymousUser').delete()
