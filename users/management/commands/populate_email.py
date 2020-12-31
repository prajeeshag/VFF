from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils.crypto import get_random_string


class Command(BaseCommand):
    help = 'Populate email field with random email address for existing users'

    def add_arguments(self, parser):
        parser.add_argument('--resetall', action='store_true',
                            help='resets all email ids')

    def handle(self, *args, **kwargs):
        User = get_user_model()
        users = User.objects.all()
        resetall = kwargs['resetall']
        for user in users:
            if not user.is_staff and (resetall or not user.email):
                user.email = user.username+'@example.com'
                user.email_verified = True
                user.verification_email_send = False
                user.save()
                print("Email for user {} set as {}".format(
                    user.username, user.email))
