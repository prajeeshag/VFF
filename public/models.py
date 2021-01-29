from django.db import models

from guardian.models import UserObjectPermissionBase
from guardian.models import GroupObjectPermissionBase


class CarouselItem(models.Model):
    color_choices = (
        ('dark', 'dark'),
        ('light', 'light'),
    )
    image = models.ImageField(
        upload_to='public/carousel_images/', max_length=255)
    caption_head = models.CharField(max_length=100, blank=True)
    caption_label = models.CharField(max_length=300, blank=True)
    caption_color = models.CharField(
        max_length=20, default='white', choices=color_choices)
    link = models.CharField(max_length=300, blank=True)
    active = models.BooleanField(default=True)
