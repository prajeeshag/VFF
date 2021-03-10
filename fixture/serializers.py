
from rest_framework import serializers

from users.models import ClubProfile, Grounds
from .models import Matches


class FixtureInputSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClubProfile
        fields = ['pk', 'home_ground', 'abbr', ]


class MatchInputSerializer(serializers.ModelSerializer):
    class Meta:
        model = Matches
        fields = ['home', 'away', 'status', 'date']
