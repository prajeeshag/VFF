from django.db import transaction
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

from fixture.models import Matches
from .models import Result, Substitution, Squad
from core.utils import disable_for_loaddata


@receiver(post_save, sender=Matches)
@disable_for_loaddata
def create_result(sender, instance, created, **kwargs):
    if not Result.objects.filter(match=instance).exists():
        Result.create(match=instance)


@receiver(pre_delete, sender=Substitution)
def reset_squad_sub(sender, instance, **kwargs):
    with transaction.atomic():
        playing_sqd = instance.squad.get_playing_squad()
        onbench_sqd = instance.squad.get_onbench_squad()
        tobench_sqd = instance.squad.get_tobench_squad()
        sub_in = instance.sub_in
        sub_out = instance.sub_out
        playing_sqd.add_player(sub_out)
        playing_sqd.remove_player(sub_in)
        onbench_sqd.add_player(sub_in)
        tobench_sqd.remove_player(sub_out)
