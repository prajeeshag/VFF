from django.db import models

from users.models import ClubProfile
from fixture.models import Matches
from match.models import Result


class ClubStat(models.Model):
    club = models.OneToOneField(
        ClubProfile, on_delete=models.PROTECT, related_name='stats')
    played = models.PositiveIntegerField(default=0)
    win = models.PositiveIntegerField(default=0)
    draw = models.PositiveIntegerField(default=0)
    loss = models.PositiveIntegerField(default=0)
    goals_for = models.PositiveIntegerField(default=0)
    goals_against = models.PositiveIntegerField(default=0)
    goal_difference = models.IntegerField(default=0)
    points = models.PositiveIntegerField(default=0)
    standing_points = models.DecimalField(default=0)

    @classmethod
    def create(cls, club):
        obj = cls.objects.get_or_create(club=club)
        obj.update()
        return obj

    def update(self):
        club = self.club
        self.played = Matches.get_done_matches_of_club(club).count()
        self.win = club.wins.all().count()
        self.loss = club.losses.all().count()
        self.draw = club.draws.all().count()
        self.goals_for = club.goals.all().count()
        self.goals_against = club.goals_against.all().count()
        self.goal_difference = self.goals_for - self.goals_against
        self.points = int(self.win * 3 + self.draw)
        self.save()

    def get_points_in_group(self, group):
        club = self.club
        grp = [g.club for g in group]
        played = Matches.objects.filter(Q(home__in=grp) | Q(
            away__in=grp)).filter(Q(home=club) | Q(away=club))
        win = club.wins.filter(loser__in=grp).count()
        loss = club.losses.filter(winner__in=grp).count()
        draw = played-win-loss
        points = int(win*3 + draw)
        return points

    @classmethod
    def update_standings(self):
        pass
