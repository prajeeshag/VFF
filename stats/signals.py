from django.db.models.signals import post_save
from django.dispatch import receiver
from guardian.shortcuts import assign_perm, remove_perm

from users.models import ClubProfile, PlayerProfile
from fixture.models import Matches
from .models import ClubStat, PlayerStat
from core.utils import disable_for_loaddata


@receiver(post_save, sender=ClubProfile)
@disable_for_loaddata
def create_club_stat(sender, instance, created, **kwargs):
    if not ClubStat.objects.filter(club=instance).exists():
        ClubStat.create(instance)
        obj.update()


@receiver(post_save, sender=PlayerProfile)
@disable_for_loaddata
def create_club_stat(sender, instance, created, **kwargs):
    if not PlayerStat.objects.filter(player=instance).exists():
        obj = PlayerStat.objects.create(player=instance)
        obj.update()
