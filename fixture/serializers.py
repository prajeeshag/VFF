
from rest_framework import serializers

from users.models import ClubProfile, Grounds


class FixtureInputSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClubProfile
        fields = ['pk', 'home_ground', 'abbr']
