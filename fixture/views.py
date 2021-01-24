
from rest_framework import viewsets
from .serializers import FixtureInputSerializer

from users.models import ClubProfile as Club


class FixtureInputApi(viewsets.ReadOnlyModelViewSet):
    queryset = Club.objects.filter(registered=True)
    serializer_class = FixtureInputSerializer
