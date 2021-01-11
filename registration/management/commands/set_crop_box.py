from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils.crypto import get_random_string

from registration.models import ProfilePicture
from myapp.utils import faceCrop
import cv2


class Command(BaseCommand):
    help = 'Set a square cropbox with face as center'

    def add_arguments(self, parser):
        parser.add_argument('--reset', action='store_true',
                            help='resets all cropbox')

    def handle(self, *args, **kwargs):
        reset = kwargs['reset']
        dps = ProfilePicture.objects.all()
        for dp in dps:
            if reset:
                dp.x1 = 0
                dp.x2 = 0
                dp.y1 = 0
                dp.y2 = 0
                dp.save()
                continue

            if dp.x2 == 0:
                x1, y1, w1, h1 = faceCrop(dp.image.path)
                if x1 is None:
                    print('No faces detected in file: '+dp.image.path)
                    continue
                x2 = x1 + w1
                y2 = y1 + h1

                dp.x1 = x1
                dp.x2 = x2
                dp.y1 = y1
                dp.y2 = y2
                dp.save()
