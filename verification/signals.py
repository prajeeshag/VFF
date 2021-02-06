from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from guardian.shortcuts import assign_perm, remove_perm

from users.models import PlayerProfile, Document
from .models import Verification


@receiver(post_save, sender=PlayerProfile)
def create_verification(sender, instance, created, **kwargs):
    if not hasattr(instance, 'verification'):
        Verification.objects.create(profile=PlayerProfile)


@receiver(pre_save, sender=PlayerProfile)
def create_review_submit1(sender, instance, created, **kwargs):
    if instance.pk:
        previous = PlayerProfile.objects.get(pk=instance.pk)
        if previous.dob != instance.dob:
            if instance.verification.need_review():
                instance.verification.review_submitted = True
                instance.verification.status = instance.verification.PENDING
                instance.verification.save()


@receiver(pre_save, sender=Document)
def create_review_submit2(sender, instance, created, **kwargs):
    if instance.pk:
        previous = PlayerProfile.objects.get(pk=instance.pk)
        if previous.image != instance.image:
            try:
                verification = instance.collection.playerprofile.verification
                if verification.need_review():
                    verification.review_submitted = True
                    verification.status = verification.PENDING
                    verification.save()
            except AttributeError:
                pass
