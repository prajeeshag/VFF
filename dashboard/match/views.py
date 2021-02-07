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

from lock_tokens.exceptions import AlreadyLockedError, UnlockForbiddenError
from lock_tokens.sessions import check_for_session, lock_for_session, unlock_for_session

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
from match.models import Squad, MatchTimeLine, Goal, Cards
from users.models import PlayerProfile, ClubProfile
from .forms import DateTimeForm

LOGIN_URL = reverse_lazy('login')

urlpatterns = []


class ManageMatchList(LoginRequiredMixin, viewMixins, TemplateView):
    template_name = 'dashboard/match/manage_match_list.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['fixed_matches'] = Matches.fixed.all()
        ctx['tentative_matches'] = Matches.tentative.all()
        ctx['done_matches'] = Matches.done.all()
        return ctx


urlpatterns += [path('managematches/',
                     ManageMatchList.as_view(),
                     name='managematches'), ]


class AddFirstTeam(LoginRequiredMixin, viewMixins, View):
    template_name = 'dashboard/match/add_first_team.html'

    def dispatch(self, request, *args, **kwargs):
        user = request.user
        club_pk = kwargs.get('club', None)
        match_pk = kwargs.get('match', None)
        match = get_object_or_404(Matches, pk=match_pk)
        club = get_object_or_404(ClubProfile, pk=club_pk)

        try:
            squad = Squad.get_squad(match, club)
        except Squad.DoesNotExist:
            squad = Squad.create(match, club, user)

        if not squad.is_pre:
            messages.add_message(
                request, messages.INFO,
                "Already finalized the squad")
            return redirect(squad)

        self.squad = squad
        self.user = user
        self.club = club
        self.match = match
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *arg, **kwargs):
        try:
            lock_for_session(self.squad, request.session)
        except AlreadyLockedError:
            messages.add_message(
                request, messages.INFO,
                "Someone else has locked squad editing!!")
            return redirect(self.backurl)

        ctx = self.get_context_data(**kwargs)
        ctx['squad'] = self.squad
        return render(request, self.template_name, ctx)

    def post(self, request, *args, **kwargs):
        if not check_for_session(self.squad, request.session):
            messages.add_message(
                request, messages.INFO,
                "Someone else has locked squad editing!")
            return redirect(self.backurl)

        action = request.POST.get('action')
        pk = request.POST.get('pk')
        player = get_object_or_404(PlayerProfile, pk=pk)

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
                    "Cannot add this player, player got pending suspension")

        elif action == 'rm':
            self.squad.remove_player_from_first(player)
        else:
            return HttpResponseNotFound('<h1>Unknown action</h1>')

        ctx = self.get_context_data(**kwargs)
        ctx['squad'] = self.squad
        unlock_for_session(self.squad, request.session)
        return render(request, self.template_name, ctx)


urlpatterns += [path('addfirstteam/<int:match>/<int:club>/',
                     AddFirstTeam.as_view(),
                     name='addfirstteam'), ]


class AddSubTeam(AddFirstTeam):
    template_name = 'dashboard/match/add_sub_team.html'

    def post(self, request, *args, **kwargs):
        if not check_for_session(self.squad, request.session):
            messages.add_message(
                request, messages.INFO,
                "Someone else has locked squad editing!")
            return redirect(self.backurl)
        action = request.POST.get('action')
        pk = request.POST.get('pk')
        player = get_object_or_404(PlayerProfile, pk=pk)
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
                    "Cannot add this player, player got pending suspension")
        elif action == 'rm':
            self.squad.remove_player_from_bench(player)
        else:
            return HttpResponseNotFound('<h1>Unknown action</h1>')

        ctx = self.get_context_data(**kwargs)
        ctx['squad'] = self.squad
        unlock_for_session(self.squad, request.session)
        return render(request, self.template_name, ctx)


urlpatterns += [path('addsubteam/<int:match>/<int:club>/',
                     AddSubTeam.as_view(),
                     name='addsubteam'), ]


class FinalizeSquad(AddFirstTeam):
    template_name = 'dashboard/match/finalize_squad.html'

    def post(self, request, *args, **kwargs):
        if not check_for_session(self.squad, request.session):
            messages.add_message(
                request, messages.WARNING,
                "Someone else has locked squad editing!")
            return redirect(self.backurl)

        self.squad.finalize()
        messages.add_message(
            request, messages.INFO,
            "You have finalized the squad")
        unlock_for_session(self.squad, request.session)
        return redirect(self.squad)


urlpatterns += [path('finalizesquad/<int:match>/<int:club>/',
                     FinalizeSquad.as_view(),
                     name='finalizesquad'), ]


class EnterPastMatchDetails(LoginRequiredMixin, viewMixins, DetailView):
    template_name = 'dashboard/match/enter_past_match_details.html'
    model = Matches

    def get(self, request, *args, **kwargs):
        match = self.get_object()
        if not match.is_fixed():
            messages.add_message(
                request, messages.WARNING,
                "Cannot Enter match details. This match is either tentative or finalized!")
            return redirect(self.backurl)
        return super().get(request, *args, **kwargs)


urlpatterns += [path('enterpastmatchdetails/<int:pk>/',
                     FinalizeSquad.as_view(),
                     name='enterpastmatchdetails'), ]


class EnterMatchTimes(LoginRequiredMixin, formviewMixins, UpdateView):
    model = MatchTimeLine
    fields = ['first_half_start', 'first_half_end',
              'second_half_start', 'second_half_end']
    template_name = 'dashboard/match/base_form.html'

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        try:
            lock_for_session(obj, request.session)
        except AlreadyLockedError:
            messages.add_message(
                request, messages.INFO,
                "Someone else has locked MatchTimeLine for editing!!")
            return redirect(self.backurl)
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        if not check_for_session(obj, request.session):
            messages.add_message(
                request, messages.INFO,
                "Someone else has locked MatchTimeLine for editing!!")
            return redirect(self.backurl)
        return super().post(request, *args, **kwargs)


urlpatterns += [path('entermatchtimes/<int:pk>/',
                     EnterMatchTimes.as_view(),
                     name='entermatchtimes'), ]
