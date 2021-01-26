
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils.crypto import get_random_string
from users.models import ClubProfile, PlayerCount, PlayerProfile, ClubSignings


class Command(BaseCommand):
    help = 'Populate player offers'

    def handle(self, *args, **kwargs):
        # Create playercount
        for club in ClubProfile.objects.all():
            playercount = getattr(club, 'playercount', None)
            if not playercount:
                PlayerCount.objects.create(club=club)
            else:
                playercount.count = 0
                playercount.save()

        ClubSignings.objects.all().delete()

        # create club signings
        for player in PlayerProfile.objects.all():
            if player.club:
                club = player.club
                playercount = club.playercount
                accepted = True
                signings, created = ClubSignings.objects.get_or_create(
                    club=club, player=player)
                signings.accept()
                print('{} Signined with {}'.format(player, club))
