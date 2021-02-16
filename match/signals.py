from django.db.models.signals import post_save
from django.dispatch import receiver
from guardian.shortcuts import assign_perm, remove_perm

from fixture.models import Matches
from .models import Result
from core.utils import disable_for_loaddata


@receiver(post_save, sender=Matches)
@disable_for_loaddata
def create_result(sender, instance, created, **kwargs):
    if not Result.objects.filter(match=instance).exists():
        Result.create(match=instance)
