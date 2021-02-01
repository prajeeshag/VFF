from django.db import models

from users.models import PlayerProfile, ClubProfile


class player(models.Model):
    profile = models.OneToOneField(PlayerProfile, on_delete=models.CASCADE)


class squad(models.Model):
    team = 
