from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils.crypto import get_random_string

from registration.models import ProfilePicture, AddressProof, AgeProof, JerseyPicture


class Command(BaseCommand):
    help = 'Set a square cropbox with face as center'

    def add_arguments(self, parser):
        parser.add_argument('--reset', action='store_true',
                            help='resets all cropbox')

    def handle(self, *args, **kwargs):
        dps = ProfilePicture.objects.all()
        i = 0
        for dp in dps:
            print(dp.pk)
            print(dp.image.name)
            dp.save(set_orientation=True)
