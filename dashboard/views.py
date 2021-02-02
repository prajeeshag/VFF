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


class Home(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/home.html'
    login_url = LOGIN_URL

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        club = user.get_club()
        if club:
            ctx['upcoming_matches'] = \
                Matches.get_upcoming_matches_of_club(club)

        if user.is_player():
            if not club:
                profile = user.get_profile()
                if profile:
                    ctx['club_offers'] = profile.get_all_offers()

        if user.is_club():
            ctx['players_no_account'] = get_objects_for_user(
                user, 'edit', klass=PlayerProfile)
            ctx['player_quota'] = club.player_quota_left()

            if not user.get_club().logo:
                messages = [
                    {'info': 'Please upload your club logo...',
                     'url': reverse_lazy('users:updateclubprofile'),
                     'url_name': 'Upload club logo'
                     }
                ]
                ctx['msgs'] = messages
        return ctx


urlpatterns += [path('home/', Home.as_view(), name='home'), ]


class UpdateEmail(LoginRequiredMixin,
                  RedirectToPreviousMixin,
                  UpdateView):
    model = get_user_model()
    form_class = forms.EmailForm
    template_name = 'dashboard/base_form.html'

    def get_object(self):
        return self.request.user


urlpatterns += [path('editemail/', UpdateEmail, name='editemail'), ]


@ require_http_methods(['POST'])
@ login_required
def EditPhoneNumber(request, pk):
    url = request.META.get('HTTP_REFERER', "/")
    form = forms.PhoneNumberForm(request.POST)
    print(request.POST)
    profile = PlayerProfile.objects.get(pk=pk)
    if form.is_valid():
        number = form.cleaned_data.get('phone_number')
        phone_number, created = PhoneNumber.objects.get_or_create(
            number=number)
        if created:
            profile.phone_number = phone_number
            profile.save()
            return HttpResponseRedirect(url)

        user = getattr(phone_number, 'user', None)
        if user:
            messages.add_message(
                request,
                messages.WARNING,
                _("Cannot change number, a profile with this number already exist"))
            return HttpResponseRedirect(url)

        return HttpResponseRedirect(url)


urlpatterns += [path('playernumber/<int:pk>',
                     EditPhoneNumber, name='editphone'), ]


class EditPlayer(SuccessMessageMixin,
                 LoginRequiredMixin,
                 RedirectToPreviousMixin,
                 UpdateView):
    model = PlayerProfile
    template_name = 'dashboard/base_form.html'
    login_url = LOGIN_URL
    success_message = 'Profile updated'

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if not request.user.has_perm('edit', obj):
            return PermissionDenied
        return super().dispatch(request, *args, **kwargs)


urlpatterns += [path('editplayer/<int:pk>',
                     EditPlayer.as_view(),
                     name='editplayer'), ]


@ require_http_methods(['POST'])
@ login_required
def del_player(request, pk):
    url = request.META.get('HTTP_REFERER', "/")
    try:
        player = PlayerProfile.objects.get(pk=pk)
    except PlayerProfile.DoesNotExist:
        messages.add_message(
            request, messages.WARNING,
            _("Couldn't Delete the player"))
        return HttpResponseRedirect(url)

    if player.user:
        messages.add_message(
            request, messages.WARNING,
            _("You can't delete this player"))
        return HttpResponseRedirect(url)

    club = request.user.get_club()
    if club:
        if club.release_player(player):
            player.delete()
        else:
            messages.add_message(
                request, messages.WARNING,
                _("Couldn't release player"))
            return HttpResponseRedirect(url)

    messages.add_message(
        request, messages.WARNING,
        _("Deleted player"))
    return HttpResponseRedirect(url)


urlpatterns += [path('delplayer/<int:pk>/',
                     del_player, name='delplayer'), ]


class Calendar(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/calendar.html'
    login_url = LOGIN_URL

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['matches'] = Matches.get_upcoming_matches()
        ctx['done_matches'] = Matches.get_done_matches()
        return ctx


urlpatterns += [path('calendar/', Calendar.as_view(), name='calendar'), ]
