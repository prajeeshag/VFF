from django.utils.decorators import method_decorator
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.base import TemplateView
from django.views.generic.detail import DetailView
from django.urls import reverse_lazy, reverse
from django import forms
from django.template import loader
from django.utils.safestring import mark_safe
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.http import HttpResponseForbidden
from django.contrib.auth import get_user_model
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.tokens import default_token_generator

from extra_views import UpdateWithInlinesView, InlineFormSetFactory, ModelFormSetView

from core.mixins import RedirectToPreviousMixin

from . import models


class Home(LoginRequiredMixin, TemplateView):
    template_name = 'users/home.html'
    login_url = reverse_lazy('login')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_club():
            return redirect(reverse('users:clublist'))
        if request.user.get_profile():
            profile = request.user.get_profile()
            return redirect(profile.get_absolute_url())
        return super().dispatch(request, *args, **kwargs)

    def get_template_names(self):
        template = super().get_template_names()

        if not self.request.user.is_staff and not self.request.user.get_profile():
            return ['page_underconstruction.html']
        return template


class ClubList(LoginRequiredMixin, TemplateView):
    template_name = 'users/club_list.html'
    login_url = reverse_lazy('login')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['clubs'] = models.ClubProfile.objects.filter(user__is_active=True)
        return ctx


class ClubMembersList(LoginRequiredMixin, DetailView):
    model = models.ClubProfile
    template_name = 'users/club_members_list.html'
    login_url = reverse_lazy('login')


class ClubDetails(LoginRequiredMixin, DetailView):
    template_name = 'users/club_details.html'
    login_url = reverse_lazy('login')
    model = models.ClubProfile

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        return ctx


class ClubOfficialsProfile(LoginRequiredMixin, DetailView):
    template_name = 'users/club_officials_profile.html'
    login_url = reverse_lazy('login')
    model = models.ClubOfficialsProfile

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        return ctx


class PlayersProfile(LoginRequiredMixin, DetailView):
    template_name = 'users/players_profile.html'
    login_url = reverse_lazy('login')
    model = models.PlayerProfile

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        return ctx


class UpdateClubProfile(LoginRequiredMixin, SuccessMessageMixin,
                        RedirectToPreviousMixin, UpdateView):
    model = models.ClubProfile
    fields = ['address', 'pincode', 'year_of_formation', 'abbr']
    login_url = reverse_lazy('login')
    template_name = 'users/club_profile_form.html'
    success_message = 'Club details has been updated'

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if not self.request.user.is_superuser and obj.user != self.request.user:
            return HttpResponseForbidden()
        return super().dispatch(request, *args, **kwargs)


class PlayersProfileUpdate(LoginRequiredMixin, SuccessMessageMixin,
                           RedirectToPreviousMixin, UpdateView):
    model = models.PlayerProfile
    fields = ['first_name', 'last_name',
              'dob', 'address', 'phone_number']
    template_name = 'users/players_profile_form.html'

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if (not self.request.user.is_staff and
                obj.club.user != self.request.user):
            return HttpResponseForbidden()
        return super().dispatch(request, *args, **kwargs)


class PlayersProfileCreate(LoginRequiredMixin, SuccessMessageMixin,
                           RedirectToPreviousMixin, CreateView):

    model = models.PlayerProfile
    fields = ['first_name', 'last_name',
              'dob', 'address', ]
    template_name = 'users/players_profile_form.html'

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if (not self.request.user.is_staff and
                obj.club.user != self.request.user):
            return HttpResponseForbidden()
        return super().dispatch(request, *args, **kwargs)


class ClubOfficialsProfileUpdate(LoginRequiredMixin, SuccessMessageMixin,
                                 RedirectToPreviousMixin, UpdateView):
    model = models.ClubOfficialsProfile
    fields = ['first_name', 'last_name',
              'dob', 'address', 'phone_number']
    template_name = 'users/club_officials_profile_form.html'

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if (not self.request.user.is_staff and
                obj.club.user != self.request.user):
            return HttpResponseForbidden()
        return super().dispatch(request, *args, **kwargs)


class abbrUpdateView(LoginRequiredMixin, RedirectToPreviousMixin, UpdateView):
    model = models.ClubProfile
    fields = ['abbr', ]
    template_name = 'users/abbr_form.html'
