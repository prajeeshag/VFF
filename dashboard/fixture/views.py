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

from core.mixins import RedirectToPreviousMixin
from formtools.wizard.views import SessionWizardView

from fixture.models import Matches
from users.models import PlayerProfile, PhoneNumber
from . import forms

LOGIN_URL = reverse_lazy('login')

urlpatterns = []


@ require_http_methods(['POST'])
@ login_required
def fixMatches(request):
    pass


urlpatterns += [path('fixmatches/',
                     fixMatches, name='fixmatches'), ]
