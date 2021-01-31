from django.db import models

from guardian.models import UserObjectPermissionBase
from guardian.models import GroupObjectPermissionBase


class Carousel(models.Model):
    name = models.CharField(max_length=20, unique=True)
    title = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.name


class CarouselItem(models.Model):
    color_choices = (
        ('dark', 'dark'),
        ('light', 'light'),
    )
    image = models.ImageField(
        upload_to='public/carousel_images/',
        max_length=255, blank=True, null=True)
    caption_head = models.CharField(max_length=100, blank=True)
    caption_label = models.CharField(max_length=300, blank=True)
    caption_color = models.CharField(
        max_length=20, default='dark',
        choices=color_choices)
    link = models.CharField(max_length=300, blank=True)
    active = models.BooleanField(default=True)
    test = models.BooleanField(default=False)
    cycles = models.PositiveIntegerField(default=1)
