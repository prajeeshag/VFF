from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

from django.utils.translation import ugettext_lazy as _


class User(AbstractUser):
    CLUB = 'CLUB'
    PERSONAL = 'PERSONAL'

    ACCOUNT_TYPE_CHOICES = [
        (CLUB, _('Club Account')),
        (PERSONAL, _('Personal Account (For players/officials)')),
    ]
    email = models.EmailField(_('Email'), unique=True, blank=False)
    user_type = models.CharField(_('User type'), max_length=10,
                                 choices=ACCOUNT_TYPE_CHOICES, default=PERSONAL)

    class Meta:
        db_table = 'auth_user'

    def is_club(self):
        return self.user_type == self.CLUB

    def is_personal(self):
        return self.user_type == self.PERSONAL
