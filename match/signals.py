from django.db import transaction
from django.db.models.signals import post_save, pre_delete, pre_save, post_delete
from django.dispatch import receiver

from fixture.models import Matches
from .models import Result, Substitution, Squad, TimeEvents, MatchTimeLine, Cards
from core.utils import disable_for_loaddata


@receiver(pre_delete, sender=Cards)
def delete_red(sender, instance, **kwargs):

    if instance.color == Cards.COLOR.red:
        with transaction.atomic():
            yellows = instance.yellows.all().order_by('pk')
            if yellows.count() > 1:
                yellow = yellows.last()
                yellow.red = None
                yellow.save()
                yellow.delete()


@receiver(post_delete, sender=Cards)
def delete_yellow(sender, instance, **kwargs):
    if instance.color != Cards.COLOR.yellow:
        return

    if instance.red:
        instance.red.delete()


@receiver(pre_delete, sender=Substitution)
def reset_squad_sub(sender, instance, **kwargs):
    with transaction.atomic():
        playing_sqd = instance.squad.get_playing_squad()
        onbench_sqd = instance.squad.get_onbench_squad()
        sub_in = instance.sub_in
        sub_out = instance.sub_out
        playing_sqd.add_player(sub_out)
        playing_sqd.remove_player(sub_in)
        onbench_sqd.add_player(sub_in)


@receiver(pre_save, sender=Substitution)
@disable_for_loaddata
def do_sub(sender, instance, **kwargs):
    playing_sqd = instance.squad.get_playing_squad()
    onbench_sqd = instance.squad.get_onbench_squad()
    played_sqd = instance.squad.get_played_squad()

    try:
        old_instance = Substitution.objects.get(pk=instance.pk)
    except Substitution.DoesNotExist:
        with transaction.atomic():
            playing_sqd.add_player(instance.sub_in)
            playing_sqd.remove_player(instance.sub_out)
            onbench_sqd.remove_player(instance.sub_in)
            played_sqd.add_player(instance.sub_in)
            instance.squad.check_nU()
            return

    if old_instance.sub_in != instance.sub_in:
        with transaction.atomic():
            playing_sqd.add_player(instance.sub_in)
            played_sqd.add_player(instance.sub_in)
            onbench_sqd.remove_player(instance.sub_in)
            playing_sqd.remove_player(old_instance.sub_in)
            played_sqd.remove_player(old_instance.sub_in)
            onbench_sqd.add_player(old_instance.sub_in)

    if old_instance.sub_out != instance.sub_out:
        with transaction.atomic():
            playing_sqd.remove_player(instance.sub_out)
            playing_sqd.add_player(old_instance.sub_out)
