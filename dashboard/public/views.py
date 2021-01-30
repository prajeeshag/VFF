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

from core.mixins import RedirectToPreviousMixin, coreMixins
from formtools.wizard.views import SessionWizardView

from public.models import CarouselItem

LOGIN_URL = reverse_lazy('login')

urlpatterns = []


class CarouselList(LoginRequiredMixin,
                   coreMixins,
                   ListView):
    model = CarouselItem
    template_name = 'dashboard/public/home.html'
    extra_context = {'title': 'Carousels Items'}


urlpatterns += [path('carosel/', CarouselList.as_view(), name='carosel'), ]


class DeleteCarouselItem(LoginRequiredMixin,
                         coreMixins,
                         DeleteView):
    model = CarouselItem
    template_name = 'dashboard/base_form.html'
    extra_context = {'title': 'Delete Carousel Items'}


urlpatterns += [path('caroselD/',
                     DeleteCarouselItem.as_view(),
                     name='caroselD'), ]


class CreateCarouselItem(LoginRequiredMixin,
                         coreMixins,
                         CreateView):
    model = CarouselItem
    fields = '__all__'
    template_name = 'dashboard/base_form.html'
    extra_context = {'title': 'Create Carousel Item'}


urlpatterns += [path('createcarosel/',
                     CreateCarouselItem.as_view(),
                     name='createcarosel'), ]
