from django.db import models
from django.db.models import Count

from users.models import ClubProfile, PlayerProfile
from fixture.models import Matches
from match.models import Result, Cards, Goal


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

    def __str__(self):
        'Stat of {}'.format(self.club)

    @classmethod
    def update_match(cls, match):
        for club in [match.home, match.away]:
            obj, created = cls.objects.get_or_create(club=club)
            obj.update()

    @classmethod
    def create(cls, club):
        obj, created = cls.objects.get_or_create(club=club)
        return obj

    @classmethod
    def create_all(cls):
        clubs = ClubProfile.objects.select_related('stats').all()
        for club in clubs:
            if not hasattr(club, 'stats'):
                obj, created = cls.objects.get_or_create(club=club)

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

    def save(self, *args, **kwargs):
        self.draw = self.played - self.win - self.loss
        self.goal_difference = self.goals_for - self.goals_against
        self.points = self.win * 3 + self.draw
        super().save(*args, **kwargs)

    @classmethod
    def update_all(cls):
        for stat in cls.objects.all():
            stat.update()

    @classmethod
    def update_standings(self):
        pass

    def do_sort(self, inp):
        """
        inp is a list, return will be a list if completely sorted
        else will be list of list.
        """
        pass


class PlayerStat(models.Model):
    player = models.OneToOneField(
        PlayerProfile,
        on_delete=models.CASCADE,
        related_name='stats')
    goals = models.PositiveIntegerField(default=0)
    yellow = models.PositiveIntegerField(default=0)
    red = models.PositiveIntegerField(default=0)

    @classmethod
    def create(cls, player):
        obj, created = cls.objects.get_or_create(player=player)
        return obj

    def update(self):
        self.goals = self.player.num_goals()
        self.yellow = Cards.objects.filter(
            is_removed=False,
            color=Cards.COLOR.yellow,
            player=self.player).count()
        self.red = Cards.objects.filter(
            is_removed=False,
            color=Cards.COLOR.red,
            player=self.player).count()
        self.save()

    @classmethod
    def update_match(cls, match):
        cls.update_all()

    @classmethod
    def create_all(cls):
        players = PlayerProfile.objects.all()
        for player in players:
            cls.create(player)

    @classmethod
    def update_all(cls, match=None):
        reds = Cards.objects.filter(
            color=Cards.COLOR.red, is_removed=False).values(
            'player').annotate(num=Count('player'))
        yellows = Cards.objects.filter(
            color=Cards.COLOR.yellow, is_removed=False).values(
            'player').annotate(num=Count('player'))
        goals = Goal.objects.filter(own=False).values(
            'player').annotate(num=Count('player'))

        num_red = {obj['player']: obj['num'] for obj in reds}
        num_yellow = {obj['player']: obj['num'] for obj in yellows}
        num_goals = {obj['player']: obj['num'] for obj in goals}

        keys = list(set(list(num_red)) | set(
            list(num_yellow)) | set(list(num_goals)))

        stats = cls.objects.filter(
            player__pk__in=keys).select_related()

        for stat in stats:
            stat.goals = num_goals.get(stat.player.pk, 0)
            stat.red = num_red.get(stat.player.pk, 0)
            stat.yellow = num_yellow.get(stat.player.pk, 0)
            stat.save()
