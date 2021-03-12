from django.db import transaction
from django.db.models.signals import post_save, pre_delete, pre_save
from django.dispatch import receiver

from fixture.models import Matches
from .models import Result, Substitution, Squad
from core.utils import disable_for_loaddata


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


@receiver(pre_save, sender=Substitution)
@disable_for_loaddata
def do_sub(sender, instance, **kwargs):
    playing_sqd = instance.squad.get_playing_squad()
    onbench_sqd = instance.squad.get_onbench_squad()
    tobench_sqd = instance.squad.get_tobench_squad()

    try:
        old_instance = Substitution.objects.get(pk=instance.pk)
    except Substitution.DoesNotExist:
        with transaction.atomic():
            playing_sqd.add_player(instance.sub_in)
            playing_sqd.remove_player(instance.sub_out)
            onbench_sqd.remove_player(instance.sub_in)
            tobench_sqd.add_player(instance.sub_out)
            instance.squad.check_nU()
            return

    if old_instance.sub_in != instance.sub_in:
        with transaction.atomic():
            playing_sqd.add_player(instance.sub_in)
            onbench_sqd.remove_player(instance.sub_in)
            playing_sqd.remove_player(old_instance.sub_in)
            onbench_sqd.add_player(old_instance.sub_in)

    if old_instance.sub_out != instance.sub_out:
        with transaction.atomic():
            playing_sqd.remove_player(instance.sub_out)
            tobench_sqd.add_player(instance.sub_out)
            playing_sqd.add_player(old_instance.sub_out)
            tobench_sqd.remove_player(old_instance.sub_out)
