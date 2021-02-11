
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils.crypto import get_random_string
from users.models import ClubProfile, PlayerCount, PlayerProfile, ClubSignings
from django.contrib.auth.models import Group


class Command(BaseCommand):
    help = 'Add club user to club_admin group'

    def handle(self, *args, **kwargs):
        # Create playercount
        club_admin_group = Group.objects.get(name='club_admins')
        for club in ClubProfile.objects.all():
            if club.user:
                club_admin_group.user_set.add(club.user)
