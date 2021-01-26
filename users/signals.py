from django.db.models.signals import post_save
from django.dispatch import receiver

from . import models


@receiver(post_save, sender=models.ClubProfile)
def create_player_count(sender, instance, created, **kwargs):
    if not hasattr(instance, 'playercount'):
        models.PlayerCount.objects.create(club=instance)
