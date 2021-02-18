
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

from . import models


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
