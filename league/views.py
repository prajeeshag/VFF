
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _

from django.views.generic.edit import CreateView, UpdateView, DeleteView
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
from django.contrib.auth.decorators import user_passes_test

from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.contrib.auth import get_user_model
from django.shortcuts import redirect, render, get_object_or_404
from django.views.decorators.http import require_http_methods

from extra_views import UpdateWithInlinesView, InlineFormSetFactory, ModelFormSetView

from core.mixins import RedirectToPreviousMixin
from formtools.wizard.views import SessionWizardView
import rules

from . import models

urlpatterns = []


class ProfileManagerRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        is_profile_manager = rules.test_rule('manage_profiles', request.user)
        if not is_profile_manager:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class MatchManagerRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        is_match_manager = rules.test_rule('manage_match', request.user)
        if not is_match_manager:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)
