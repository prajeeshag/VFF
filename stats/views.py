
from django import forms
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _

from django.views.generic.edit import CreateView, UpdateView, DeleteView, FormView
from django.views.generic.base import TemplateView
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from django.views import View

from django.urls import reverse_lazy, reverse, path, include
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.views import PasswordChangeView
from django.core.exceptions import PermissionDenied

import rules
from django.http import (
    HttpResponseForbidden, HttpResponseRedirect,
    HttpResponse, HttpResponseNotFound
)

from django.contrib.auth import get_user_model
from django.shortcuts import redirect, render, get_object_or_404
from django.views.decorators.http import require_http_methods

from guardian.shortcuts import get_objects_for_user

from core.mixins import formviewMixins, viewMixins
from formtools.wizard.views import SessionWizardView

from .models import ClubStat, PlayerStat
from fixture.models import Matches
from match.views import MatchManagerRequiredMixin


LOGIN_URL = reverse_lazy('login')

urlpatterns = []


class PointTable(viewMixins, TemplateView):
    template_name = 'stats/point_table.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['stats'] = ClubStat.objects.all().order_by(
            '-points', '-goal_difference',
            '-goals_for', 'goals_against')
        return ctx


urlpatterns += [path('pointtable/',
                     PointTable.as_view(),
                     name='pointtable'), ]


class UpdateStat(MatchManagerRequiredMixin, FormView):
    template_name = 'dashboard/base_form.html'
    form_class = forms.Form

    def dispatch(self, request, *args, **kwargs):
        pk = kwargs.get('pk', None)
        self.match = get_object_or_404(Matches, pk=pk)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        ClubStat.update_all()
        PlayerStat.update_all(self.match)
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Update statistics?'
        ctx['back_url'] = reverse(
            'dash:enterpastmatchdetails', kwargs={'pk': self.match.pk})
        return ctx

    def get_success_url(self):
        return reverse('dash:enterpastmatchdetails', kwargs={'pk': self.match.pk})


urlpatterns += [path('updatestat/<int:pk>/',
                     UpdateStat.as_view(),
                     name='updatestat'), ]
