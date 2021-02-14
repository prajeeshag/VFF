from django.db.models.signals import post_save
from django.dispatch import receiver
from guardian.shortcuts import assign_perm, remove_perm

from users.models import ClubProfile
from .models import ClubStat
from core.utils import disable_for_loaddata


@receiver(post_save, sender=ClubProfile)
@disable_for_loaddata
def create_club_stat(sender, instance, created, **kwargs):
    if not hasattr(instance, 'stats'):
        ClubStat.create(instance)
