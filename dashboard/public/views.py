from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _

from django.views.generic.edit import CreateView, UpdateView, DeleteView, FormView
from django.views.generic.base import TemplateView
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView

from django.urls import reverse_lazy, reverse
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

from public.models import CarouselItem

LOGIN_URL = reverse_lazy('login')


class CreateCarouselItem(LoginRequiredMixin,
                         RedirectToPreviousMixin,
                         CreateView):
    model = CarouselItem
    fields = '__all__'
    template_name = 'dashboard/base_form.html'

    def get_context_data(self, **kwargs):
        ctx = self.get_context_data(**kwargs)
        ctx['title'] = 'Create CarouselItem'
