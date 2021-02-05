from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _

from django.views.generic.edit import CreateView, UpdateView, DeleteView, FormView
from django.views.generic.base import TemplateView
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from django.views import View

from django.urls import reverse_lazy, reverse, path, include
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.views import PasswordChangeView
from django.core.exceptions import PermissionDenied

from django.http import (
    HttpResponseForbidden, HttpResponseRedirect,
    HttpResponse, HttpResponseNotFound
)

from django.contrib.auth import get_user_model
from django.shortcuts import redirect, render, get_object_or_404
from django.views.decorators.http import require_http_methods

from guardian.shortcuts import get_objects_for_user

from extra_views import UpdateWithInlinesView, InlineFormSetFactory, ModelFormSetView

from core.mixins import formviewMixins, viewMixins
from formtools.wizard.views import SessionWizardView

from fixture.models import Matches
from league.models import Season
from match.models import Squad
from users.models import PlayerProfile

LOGIN_URL = reverse_lazy('login')

urlpatterns = []


class AddFirstTeam(LoginRequiredMixin, viewMixins, View):
    template_name = 'dashboard/match/add_first_team.html'

    def dispatch(self, request, *args, **kwargs):
        user = request.user
        if not user.is_club():
            raise PermissionDenied

        club = user.get_club()
        match = Matches.get_current_next_match_of_club(club)
        if not match:
            return HttpResponseNotFound('<h1>No next match found</h1>')

        try:
            squad = Squad.get_squad(match, club)
        except Squad.DoesNotExist:
            squad = Squad.create(match, club, user)

        if squad.lock:
            messages.add_message(
                request, messages.INFO,
                "You have already finalized the squad")
            return redirect(squad)

        self.squad = squad
        self.user = user
        self.club = club
        self.match = match

        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *arg, **kwargs):
        ctx = self.get_context_data(**kwargs)
        ctx['squad'] = self.squad
        return render(request, self.template_name, ctx)

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action')
        pk = request.POST.get('pk')
        player = get_object_or_404(PlayerProfile, pk=pk)
        if player.get_club() != self.club:
            return HttpResponseNotFound('<h1>Player not from your club</h1>')

        if action == 'add':
            try:
                self.squad.add_player_to_first(player)
            except self.squad.LimitReached:
                messages.add_message(
                    request, messages.WARNING,
                    "Reached Limit")
            except self.squad.GotSuspension:
                messages.add_message(
                    request, messages.WARNING,
                    "Cannot add this player, Player Got Suspension")

        elif action == 'rm':
            self.squad.remove_player_from_first(player)
        else:
            return HttpResponseNotFound('<h1>Unknown action</h1>')

        ctx = self.get_context_data(**kwargs)
        ctx['squad'] = self.squad
        return render(request, self.template_name, ctx)


urlpatterns += [path('addfirstteam/',
                     AddFirstTeam.as_view(),
                     name='addfirstteam'), ]


class AddSubTeam(AddFirstTeam):
    template_name = 'dashboard/match/add_sub_team.html'

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action')
        pk = request.POST.get('pk')
        player = get_object_or_404(PlayerProfile, pk=pk)
        if player.get_club() != self.club:
            return HttpResponseNotFound('<h1>Player not from your club</h1>')

        if action == 'add':
            try:
                self.squad.add_player_to_bench(player)
            except self.squad.LimitReached:
                messages.add_message(
                    request, messages.WARNING,
                    "Reached Limit")
            except self.squad.GotSuspension:
                messages.add_message(
                    request, messages.WARNING,
                    "Cannot add this player, Player Got Suspension")

        elif action == 'rm':
            self.squad.remove_player_from_bench(player)
        else:
            return HttpResponseNotFound('<h1>Unknown action</h1>')

        ctx = self.get_context_data(**kwargs)
        ctx['squad'] = self.squad
        return render(request, self.template_name, ctx)


urlpatterns += [path('addsubteam/',
                     AddSubTeam.as_view(),
                     name='addsubteam'), ]


class FinalizeSquad(AddFirstTeam):
    template_name = 'dashboard/match/finalize_squad.html'

    def post(self, request, *args, **kwargs):
        self.squad.finalize()
        messages.add_message(
            request, messages.INFO,
            "You have finalized the squad")
        return redirect(squad)


urlpatterns += [path('finalizesquad/',
                     FinalizeSquad.as_view(),
                     name='finalizesquad'), ]
