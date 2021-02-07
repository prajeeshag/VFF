from django.db.models.signals import post_save
from django.dispatch import receiver
from guardian.shortcuts import assign_perm, remove_perm

from . import models
from core.utils import disable_for_loaddata


@receiver(post_save, sender=models.ClubProfile)
@disable_for_loaddata
def create_player_count(sender, instance, created, **kwargs):
    if not hasattr(instance, 'playercount'):
        models.PlayerCount.objects.create(club=instance)


@receiver(post_save, sender=models.PlayerProfile)
def set_player_permission(sender, instance, created, **kwargs):
    user = instance.user
    club = instance.club
    if user:
        assign_perm('edit', user, instance)
        if club:
            remove_perm('edit', club.user, instance)
    elif club:
        assign_perm('edit', club.user, instance)
