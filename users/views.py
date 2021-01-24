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

from core.mixins import breadcrumbMixin, RedirectToPreviousMixin

from . import models


class ClubList(LoginRequiredMixin, breadcrumbMixin, TemplateView):
    template_name = 'users/club_list.html'
    login_url = reverse_lazy('login')
    breadcrumbs = [('Clubs', None), ]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['clubs'] = models.ClubProfile.objects.filter(user__is_active=True)
        return ctx


class ClubMembersList(LoginRequiredMixin, breadcrumbMixin, DetailView):
    model = models.ClubProfile
    template_name = 'users/club_members_list.html'
    login_url = reverse_lazy('login')
    breadcrumbs = [
        ('Clubs', 'users:clublist'),
        ('List of Members', None),
    ]


class ClubDetails(breadcrumbMixin, DetailView):
    template_name = 'users/club_details.html'
    login_url = reverse_lazy('login')
    model = models.ClubProfile
    breadcrumbs = [('Clubs', 'users:clublist'), ]

    def get_breadcrumbs(self):
        bc = super().get_breadcrumbs()
        bc.append(self.make_breadcrumbs(
            viewname='users:clubdetails', obj=self.object))
        return bc

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        return ctx


class ClubOfficialsProfile(LoginRequiredMixin, breadcrumbMixin, DetailView):
    template_name = 'users/club_officials_profile.html'
    login_url = reverse_lazy('login')
    model = models.ClubOfficialsProfile

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        return ctx

    def get_breadcrumbs(self):
        bc = super().get_breadcrumbs()
        bc.append(self.make_breadcrumbs(
            viewname='users:clubdetails', obj=self.object.club))
        bc.append(self.make_breadcrumbs(name=self.object.role))
        return bc


class PlayersProfile(LoginRequiredMixin, breadcrumbMixin, DetailView):
    template_name = 'users/players_profile.html'
    login_url = reverse_lazy('login')
    model = models.PlayerProfile

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        return ctx

    def get_breadcrumbs(self):
        bc = super().get_breadcrumbs()
        bc.append(self.make_breadcrumbs(
            viewname='users:clubdetails', obj=self.object.club))
        return bc


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
    fields = ['abbr',]
    template_name = 'users/abbr_form.html'
