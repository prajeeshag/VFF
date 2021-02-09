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

from core.mixins import formviewMixins, viewMixins
from formtools.wizard.views import SessionWizardView

from users.models import PlayerProfile
from verification.models import Verification

LOGIN_URL = reverse_lazy('login')

urlpatterns = []


class ReviewPlayerProfile(LoginRequiredMixin,
                          formviewMixins,
                          UpdateView):
    model = Verification
    fields = ['status', 'review_comment']
    template_name = 'dashboard/verification/profile_verification.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['redirect_url'] = reverse('dash:verificationlist')
        return ctx

    def form_valid(self, form):
        form.instance.last_updated_by = self.request.user
        return super().form_valid(form)


urlpatterns += [path('reviewplayerprofile/<int:pk>/',
                     ReviewPlayerProfile.as_view(),
                     name='reviewplayerprofile'), ]


class List(LoginRequiredMixin,
           viewMixins,
           TemplateView):
    template_name = 'dashboard/verification/list.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Proifle Verification: Pending'
        ctx['pending'] = Verification.objects.filter(
            status=Verification.PENDING)
        ctx['verified'] = Verification.objects.filter(
            status=Verification.VERIFIED)
        ctx['needreview'] = Verification.objects.filter(
            status=Verification.NEEDREVIEW)
        return ctx


urlpatterns += [path('list/',
                     List.as_view(),
                     name='verificationlist'), ]
