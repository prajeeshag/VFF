
from django.db.models import Q
from django.utils.decorators import method_decorator
from django.views.generic.edit import CreateView, UpdateView, DeleteView, FormView
from django.views.generic.base import TemplateView
from django.views.generic.detail import DetailView
from django.urls import reverse_lazy, reverse

from . import models
from rest_framework import viewsets
from .serializers import FixtureInputSerializer, MatchInputSerializer

from core.mixins import viewMixins, formviewMixins
from users.models import ClubProfile as Club

from .models import Matches


class FixtureInputApi(viewsets.ReadOnlyModelViewSet):
    queryset = Club.objects.filter(registered=True)
    serializer_class = FixtureInputSerializer


class MatchInputApi(viewsets.ReadOnlyModelViewSet):
    queryset = Matches.objects.filter(
        Q(status=Matches.STATUS.done) | Q(status=Matches.STATUS.fixed))
    serializer_class = MatchInputSerializer
