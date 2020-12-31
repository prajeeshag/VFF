from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils.crypto import get_random_string


class Command(BaseCommand):
    help = 'Set users user type to CLUB if user has a Club attribute'

    # def add_arguments(self, parser):
    # parser.add_argument('--resetall', action='store_true',
    # help='resets all email ids')

    def handle(self, *args, **kwargs):
        User = get_user_model()
        users = User.objects.all()
        for user in users:
            if not user.is_staff and hasattr(user, 'club'):
                user.user_type = User.CLUB
                user.save()
                print("User {} set as {}".format(
                    user.username, User.CLUB))
