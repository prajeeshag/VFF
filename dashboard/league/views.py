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

from guardian.shortcuts import get_objects_for_user

from extra_views import UpdateWithInlinesView, InlineFormSetFactory, ModelFormSetView

from core.mixins import viewMixins, formviewMixins
from formtools.wizard.views import SessionWizardView

from league.models import Season

LOGIN_URL = reverse_lazy('login')

urlpatterns = []


class SeasonDetails(LoginRequiredMixin, viewMixins, DetailView):
    model = Season
    template_name = 'dashboard/league/season_details.html'

    def get_object(self):
        return Season.objects.first()


urlpatterns += [path('seasondetails/',
                     SeasonDetails.as_view(), name='season_details'), ]


class SeasonUpdate(LoginRequiredMixin, formviewMixins, UpdateView):
    model = Season
    template_name = 'dashboard/base_form.html'
    # fields = '__all__'
    fields = ['name', 'cro_datetime', 'crc_datetime', 'twc_datetime']

    def get_object(self):
        return Season.objects.first()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = self.get_object()
        return ctx


urlpatterns += [path('seasonedit/',
                     SeasonUpdate.as_view(), name='season_edit'), ]
