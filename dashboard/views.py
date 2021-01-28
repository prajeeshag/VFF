from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _

from django.views.generic.edit import CreateView, UpdateView, DeleteView
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

from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.contrib.auth import get_user_model
from django.shortcuts import redirect, render, get_object_or_404
from django.views.decorators.http import require_http_methods

from extra_views import UpdateWithInlinesView, InlineFormSetFactory, ModelFormSetView

from core.mixins import RedirectToPreviousMixin
from formtools.wizard.views import SessionWizardView

from fixture.models import Matches
from users.models import PlayerProfile

LOGIN_URL = reverse_lazy('login')


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
            signings = club.clubsignings.filter(
                accepted=True).prefetch_related('player')
            ctx['players_no_account'] = [
                s.player for s in signings if not s.player.user]
            ctx['player_quota'] = club.player_quota_left()
        return ctx


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


class Calendar(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/calendar.html'
    login_url = LOGIN_URL

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['matches'] = Matches.get_upcoming_matches()
        return ctx
