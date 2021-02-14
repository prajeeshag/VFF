from django.db import models

from users.models import ClubProfile
from fixture.models import Matches
from match.models import Result


def get_points(self, against=None):
    nplayed = self.num_played(against)
    nwins = self.num_wins(against)
    nlosses = self.num_losses(against)
    ndraws = nplayed-(nwins+nlosses)
    return nwins*3+ndraws


setattr(ClubProfile, 'get_points', get_points)


class ClubStat(models.Model):
    club = models.OneToOneField(
        ClubProfile, on_delete=models.CASCADE,
        related_name='stats')
    played = models.PositiveIntegerField(default=0)
    win = models.PositiveIntegerField(default=0)
    draw = models.PositiveIntegerField(default=0)
    loss = models.PositiveIntegerField(default=0)
    goals_for = models.PositiveIntegerField(default=0)
    goals_against = models.PositiveIntegerField(default=0)
    goal_difference = models.IntegerField(default=0)
    points = models.PositiveIntegerField(default=0)

    @classmethod
    def create(cls, club):
        obj, created = cls.objects.get_or_create(club=club)
        obj.update()
        return obj

    def update(self):
        club = self.club
        self.played = club.num_played()
        self.win = club.num_wins()
        self.loss = club.num_losses()
        self.draw = self.played - self.win - self.loss
        self.goals_for = club.num_goals()
        self.goals_against = club.num_goals_against()
        self.goal_difference = self.goals_for - self.goals_against
        self.points = self.win * 3 + self.draw
        self.save()

    @classmethod
    def update_standings(self):
        pass

    def do_sort(self, inp):
        """
        inp is a list, return will be a list if completely sorted
        else will be list of list.
        """
        pass
