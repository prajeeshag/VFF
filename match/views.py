
from django.db.models import Count, Q, F
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _

from django.views.generic.edit import CreateView, UpdateView, DeleteView, FormView
from django.views.generic.base import TemplateView
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView

from django.urls import reverse_lazy, reverse, path, include
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.views import PasswordChangeView
from django.core.exceptions import PermissionDenied

from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.contrib.auth import get_user_model
from django.shortcuts import redirect, render, get_object_or_404
from django.views.decorators.http import require_http_methods

import rules
from guardian.shortcuts import get_objects_for_user

from extra_views import UpdateWithInlinesView, InlineFormSetFactory, ModelFormSetView

from core.mixins import formviewMixins, viewMixins
from formtools.wizard.views import SessionWizardView

from . import models, forms
from users.models import PlayerProfile


urlpatterns = []


class MatchManagerRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        is_match_manager = rules.test_rule('manage_match', request.user)
        if not is_match_manager:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class Squad(viewMixins, DeleteView):
    template_name = 'match/squad.html'
    model = models.Squad


urlpatterns += [path('squad/<int:pk>/', Squad.as_view(), name='squad'), ]


class Substitution(viewMixins, DeleteView):
    template_name = 'match/Substitution.html'
    model = models.Substitution


urlpatterns += [path('substitution/<int:pk>/',
                     Substitution.as_view(),
                     name='substitution'), ]


class MatchTimeLine(viewMixins, DetailView):
    template_name = 'match/matchtimeline.html'
    model = models.MatchTimeLine

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        return ctx


urlpatterns += [path('matchtimeline/<int:pk>/',
                     MatchTimeLine.as_view(),
                     name='matchtimeline'), ]


class SuspensionList(MatchManagerRequiredMixin, TemplateView):
    template_name = 'match/suspensions.html'

    def get_context_data(self, **kwargs):
        mdl = models.Suspension
        ctx = super().get_context_data(**kwargs)
        ctx['pending_suspensions'] = mdl.pending.all().select_related()
        ctx['other_suspensions'] = mdl.objects.exclude(
            status=mdl.STATUS.pending).select_related()
        return ctx


urlpatterns += [path('suspensions/',
                     SuspensionList.as_view(),
                     name='suspensions'), ]


class CardList(MatchManagerRequiredMixin, TemplateView):
    template_name = 'match/cards.html'

    def get_context_data(self, **kwargs):
        mdl = models.Cards
        ctx = super().get_context_data(**kwargs)
        ctx['cards'] = mdl.objects.filter(
            is_removed=False).select_related().order_by('-created')
        reds = mdl.objects.filter(
            color=mdl.COLOR.red, is_removed=False).values(
            'player').annotate(num=Count('player'))
        yellows = mdl.objects.filter(
            color=mdl.COLOR.yellow, is_removed=False).values(
            'player').annotate(num=Count('player'))
        num_red = {obj['player']: obj['num'] for obj in reds}
        num_yellow = {obj['player']: obj['num'] for obj in yellows}
        keys = list(set(list(num_red)) | set(list(num_yellow)))
        players = PlayerProfile.objects.filter(pk__in=keys)
        ctx['players'] = [{'player': player, 'num_red': num_red.get(player.pk, 0),
                           'num_yellow': num_yellow.get(player.pk, 0)} for player in players]

        return ctx


urlpatterns += [path('cards/',
                     CardList.as_view(),
                     name='cards'), ]


class EditGoal(MatchManagerRequiredMixin, UpdateView):
    model = models.Goal
    form_class = forms.EditGoalForm
    template_name = 'dashboard/base_form.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Edit Goal - {}'.format(self.object.match)
        return ctx

    def get_success_url(self):
        match = self.object.match
        return reverse('dash:enterpastmatchdetails', kwargs={'pk': match.pk})


urlpatterns += [path('editgoal/<int:pk>/',
                     EditGoal.as_view(),
                     name='editgoal'), ]
