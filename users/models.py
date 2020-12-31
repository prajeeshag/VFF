from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings


class User(AbstractUser):
    CLUB = 'CLUB'
    PERSONAL = 'PERSONAL'

    ACCOUNT_TYPE_CHOICES = [
        (CLUB, 'Club Account'),
        (PERSONAL, 'Personal Account (For players/officials)'),
    ]
    email_verified = models.BooleanField(default=False)
    verification_email_send = models.BooleanField(default=False)
    email = models.EmailField(unique=True, blank=False)
    user_type = models.CharField(
        max_length=10, choices=ACCOUNT_TYPE_CHOICES, default=PERSONAL)

    class Meta:
        db_table = 'auth_user'

    def is_club(self):
        return self.user_type == self.CLUB

    def is_personal(self):
        return self.user_type == self.PERSONAL
