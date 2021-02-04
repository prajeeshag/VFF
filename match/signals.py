from django.db.models.signals import post_save
from django.dispatch import receiver
from guardian.shortcuts import assign_perm, remove_perm

from . import models


class MatchDoesNotExist(Exception):
    pass


@receiver(post_save, sender=models.Squad)
def create_timeline_event_squad(sender, instance, created, **kwargs):
    if instance.timeline:
        match = instance.match
        if not match:
            raise MatchDoesNotExist
        timeline, created = models.MatchTimeLine.objects.get_or_create(
            match=match)
        models.Events.objects.create(
            matchtimeline=timeline,
            message=instance.timeline_message(),
            url=instance.timeline_url(),
            time=instance.timeline_time()
        )


@receiver(post_save, sender=models.Substitution)
def create_timeline_event_Substitution(sender, instance, created, **kwargs):
    if created:
        match = instance.squad.match
        if not match:
            raise MatchDoesNotExist

        timeline, created = models.MatchTimeLine.objects.get_or_create(
            match=match)

        models.Events.objects.create(
            matchtimeline=timeline,
            message=instance.timeline_message(),
            url=instance.timeline_url(),
            time=instance.timeline_time()
        )


@receiver(post_save, sender=models.Cards)
def create_timeline_event_Cards(sender, instance, created, **kwargs):
    if created:
        match = instance.match
        if not match:
            raise MatchDoesNotExist

        timeline, created = models.MatchTimeLine.objects.get_or_create(
            match=match)

        models.Events.objects.create(
            matchtimeline=timeline,
            message=instance.timeline_message(),
            url=instance.timeline_url(),
            time=instance.timeline_time()
        )
