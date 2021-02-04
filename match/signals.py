from django.db.models.signals import post_save
from django.dispatch import receiver
from guardian.shortcuts import assign_perm, remove_perm

from . import models


class MatchDoesNotExist(Exception):
    pass


@receiver(post_save, sender=models.Squad)
def create_timeline_event(sender, instance, created, **kwargs):
    if instance.released:
        match = instance.match
        if not match:
            raise MatchDoesNotExist
        timeline, created = models.MatchTimeLine.objects.get_or_create(
            match=match)
        models.Events.objects.create(
            matchtimeline=timeline,
            message=instance.timeline_message(),
            url=instance.timeline_url()
            time=instance.timeline_time()
        )


@ receiver(post_save, sender=models.PlayerProfile)
def set_player_permission(sender, instance, created, **kwargs):
    user = instance.user
    club = instance.club
    if user:
        assign_perm('edit', user, instance)
        if club:
            remove_perm('edit', club.user, instance)
    elif club:
        assign_perm('edit', club.user, instance)
