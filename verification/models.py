from django.db import models

from django.utils import timezone
from users.models import PlayerProfile


class Verification(models.Model):
    NEEDREVIEW = 'NEED REVIEW'
    VERIFIED = 'VERIFIED'
    PENDING = 'PENDING'
    status_choice = (
        (NEEDREVIEW, NEEDREVIEW),
        (VERIFIED, VERIFIED),
        (PENDING, PENDING),
    )
    profile = models.OneToOneField(PlayerProfile, on_delete=models.CASCADE)
    status = models.CharField(
        max_length=15, choices=status_choice, default=PENDING)
    review_submitted = models.BooleanField(default=False)
    review_comment = models.TextField(max_length=300, blank=True)

    def __str__(self):
        return self.status

    def is_verified(self):
        return self.status == self.VERIFIED

    def is_pending(self):
        return self.status == self.PENDING

    def need_review(self):
        return self.status == self.NEEDREVIEW
