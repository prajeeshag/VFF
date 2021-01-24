
from django.utils.decorators import method_decorator
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.base import TemplateView
from django.views.generic.detail import DetailView
from django.urls import reverse_lazy, reverse

from . import models
from rest_framework import viewsets
from .serializers import FixtureInputSerializer

from users.models import ClubProfile as Club

from . import models


class FixtureInputApi(viewsets.ReadOnlyModelViewSet):
    queryset = Club.objects.filter(registered=True)
    serializer_class = FixtureInputSerializer


