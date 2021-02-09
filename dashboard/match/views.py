
import datetime as dt

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


from core.mixins import formviewMixins, viewMixins
from formtools.wizard.views import SessionWizardView

from fixture.models import Matches
from league.models import Season
from match.models import Squad, MatchTimeLine, Goal, Cards, GoalAttr, CardReason
from users.models import PlayerProfile, ClubProfile
from .forms import DateTimeForm, MatchTimeForm

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


class EnterPastMatchDetails(LoginRequiredMixin, viewMixins, DetailView):
    template_name = 'dashboard/match/enter_past_match_details.html'
    model = Matches
    context_object_name = 'match'

    def get(self, request, *args, **kwargs):
        match = self.get_object()
        if not match.is_fixed():
            messages.add_message(
                request, messages.WARNING,
                "Cannot Enter match details. This match is either tentative or finalized!")
            return redirect(self.backurl)
        return super().get(request, *args, **kwargs)


urlpatterns += [path('enterpastmatchdetails/<int:pk>/',
                     EnterPastMatchDetails.as_view(),
                     name='enterpastmatchdetails'), ]


class AddFirstTeam(LoginRequiredMixin, viewMixins, View):
    template_name = 'dashboard/match/add_team.html'

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

        if not squad.is_pre():
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
        ctx['squad'] = self.squad.get_first_squad()
        ctx['squad_av'] = self.squad.get_avail_squad()
        ctx['stepnexturl'] = reverse('dash:addsubteam', kwargs={
                                     'club': self.club.pk, 'match': self.match.pk})
        ctx['club'] = self.club
        ctx['match'] = self.match
        request.session['add_squad_return_url'] = request.session.get(
            'previous_page', None)
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

        return redirect(self.backurl)


urlpatterns += [path('addfirstteam/<int:match>/<int:club>/',
                     AddFirstTeam.as_view(),
                     name='addfirstteam'), ]


class AddSubTeam(AddFirstTeam):
    template_name = 'dashboard/match/add_team.html'

    def get(self, request, *arg, **kwargs):
        try:
            lock_for_session(self.squad, request.session)
        except AlreadyLockedError:
            messages.add_message(
                request, messages.INFO,
                "Someone else has locked squad editing!!")
            return redirect(self.backurl)

        ctx = self.get_context_data(**kwargs)
        ctx['squad'] = self.squad.get_bench_squad()
        ctx['squad_av'] = self.squad.get_avail_squad()
        ctx['stepnexturl'] = reverse('dash:finalizesquad', kwargs={
                                     'club': self.club.pk, 'match': self.match.pk})
        ctx['stepbackurl'] = reverse('dash:addfirstteam', kwargs={
                                     'club': self.club.pk, 'match': self.match.pk})
        ctx['club'] = self.club
        ctx['match'] = self.match
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

        return redirect(self.backurl)


urlpatterns += [path('addsubteam/<int:match>/<int:club>/',
                     AddSubTeam.as_view(),
                     name='addsubteam'), ]


class FinalizeSquad(AddFirstTeam):
    template_name = 'dashboard/match/finalize_squad.html'

    def get(self, request, *arg, **kwargs):
        try:
            lock_for_session(self.squad, request.session)
        except AlreadyLockedError:
            messages.add_message(
                request, messages.INFO,
                "Someone else has locked squad editing!!")
            return redirect(self.backurl)

        ctx = self.get_context_data(**kwargs)
        ctx['squad'] = self.squad.get_first_squad()
        ctx['squad_av'] = self.squad.get_bench_squad()
        ctx['stepbackurl'] = reverse('dash:addfirstteam', kwargs={
                                     'club': self.club.pk, 'match': self.match.pk})
        ctx['club'] = self.club
        ctx['match'] = self.match
        return render(request, self.template_name, ctx)

    def post(self, request, *args, **kwargs):
        if not check_for_session(self.squad, request.session):
            messages.add_message(
                request, messages.WARNING,
                "Someone else has locked squad editing!")
            return redirect(self.backurl)
        try:
            self.squad.finalize()
        except self.squad.NotEnoughPlayers as e:
            messages.add_message(request, messages.WARNING, e)
            return redirect(self.backurl)

        if request.session.get('add_squad_return_url', None):
            return redirect(request.session.get('add_squad_return_url'))
        return redirect(self.squad)


urlpatterns += [path('finalizesquad/<int:match>/<int:club>/',
                     FinalizeSquad.as_view(),
                     name='finalizesquad'), ]


class MatchLockMixin:
    def dispatch(self, request, *args, **kwargs):
        pk = kwargs.get('pk')
        match = get_object_or_404(Matches, pk=pk)
        self.match = match
        try:
            lock_for_session(match, request.session)
        except AlreadyLockedError:
            messages.add_message(
                request, messages.INFO,
                "Someone else has locked the match!!")
            return redirect(self.backurl)
        return super().dispatch(request, *args, **kwargs)


class StartMatch(LoginRequiredMixin,
                 formviewMixins,
                 MatchLockMixin,
                 FormView):
    form_class = DateTimeForm
    template_name = 'dashboard/match/base_form.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Start Match'
        ctx['return_url'] = reverse(
            'dash:enterpastmatchdetails', kwargs={'pk': self.match.pk})
        return ctx

    def get_initial(self):
        return {'time': self.match.date}

    def form_valid(self, form):
        time = form.cleaned_data.get('time')
        if self.match.matchtimeline.first_half_start:
            messages.add_message(
                self.request, messages.DANGER,
                "Match already started!!")
        else:
            self.match.matchtimeline.start_match(time=time)
        return super().form_valid(form)

    def form_invalid(self, form):
        if self.request.POST.get('time') == 'now':
            if self.match.matchtimeline.first_half_start:
                messages.add_message(
                    self.request, messages.DANGER,
                    "Match already started!!")
            else:
                self.match.matchtimeline.start_match()
        return super().form_invalid(form)


urlpatterns += [path('startmatch/<int:pk>/',
                     StartMatch.as_view(),
                     name='startmatch'), ]


class HalfTime(LoginRequiredMixin,
               formviewMixins,
               MatchLockMixin,
               FormView):
    form_class = MatchTimeForm
    template_name = 'dashboard/match/base_form.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Half Time'
        ctx['return_url'] = reverse(
            'dash:enterpastmatchdetails', kwargs={'pk': self.match.pk})
        return ctx

    def form_valid(self, form):
        time = form.cleaned_data.get('minutes')
        time = time*60
        if self.match.matchtimeline.half_time:
            messages.add_message(
                self.request, messages.DANGER,
                "Match already in halftime!!")
        else:
            self.match.matchtimeline.set_half_time(time=time)
        return super().form_valid(form)

    def form_invalid(self, form):
        if self.request.POST.get('time') == 'now':
            if self.match.matchtimeline.half_time:
                messages.add_message(
                    self.request, messages.DANGER,
                    "Match already in halftime!!")
            else:
                self.match.matchtimeline.set_half_time()
        return super().form_invalid(form)


urlpatterns += [path('halftime/<int:pk>/',
                     HalfTime.as_view(),
                     name='halftime'), ]


class SecondHalf(LoginRequiredMixin,
                 formviewMixins,
                 MatchLockMixin,
                 FormView):
    form_class = DateTimeForm
    template_name = 'dashboard/match/base_form.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Second Half'
        ctx['return_url'] = reverse(
            'dash:enterpastmatchdetails', kwargs={'pk': self.match.pk})
        return ctx

    def get_initial(self):
        return {'time': self.match.date+dt.timedelta(hours=1)}

    def form_valid(self, form):
        time = form.cleaned_data.get('time')
        if self.match.matchtimeline.second_half_start:
            messages.add_message(
                self.request, messages.DANGER,
                "Match already started!!")
        else:
            self.match.matchtimeline.start_second_half(time=time)
        return super().form_valid(form)

    def form_invalid(self, form):
        if self.request.POST.get('time') == 'now':
            if self.match.matchtimeline.second_half_start:
                messages.add_message(
                    self.request, messages.DANGER,
                    "Match already started!!")
            else:
                self.match.matchtimeline.start_second_half()
        return super().form_invalid(form)


urlpatterns += [path('secondhalf/<int:pk>/',
                     SecondHalf.as_view(),
                     name='secondhalf'), ]


class FinalTime(LoginRequiredMixin,
                formviewMixins,
                MatchLockMixin,
                FormView):
    form_class = MatchTimeForm
    template_name = 'dashboard/match/base_form.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Final Time'
        ctx['return_url'] = reverse(
            'dash:enterpastmatchdetails', kwargs={'pk': self.match.pk})
        return ctx

    def form_valid(self, form):
        time = form.cleaned_data.get('minutes')
        time = time*60
        if self.match.matchtimeline.final_time:
            messages.add_message(
                self.request, messages.DANGER,
                "Match already in Final Time!!")
        else:
            self.match.matchtimeline.finalize_match(time=time)
        return super().form_valid(form)

    def form_invalid(self, form):
        if self.request.POST.get('time') == 'now':
            if self.match.matchtimeline.final_time:
                messages.add_message(
                    self.request, messages.DANGER,
                    "Match already in Final Time!!")
            else:
                self.match.matchtimeline.finalize_match()
        return super().form_invalid(form)


urlpatterns += [path('finaltime/<int:pk>/',
                     FinalTime.as_view(),
                     name='finaltime'), ]


# class PlayerSelect(LoginRequiredMixin,
# viewMixins,
# MatchLockMixin,
# TemplateView):

# template_name = 'dashboard/match/player_select.html'
# kind = 'goal'

# def get_context_data(self, **kwargs):
# club_pk = kwargs.get('club')
# club = get_object_or_404(ClubProfile, pk=club_pk)
# ctx = super().get_context_data(**kwargs)
# ctx['backurl'] = reverse('dash:enterpastmatchdetails', kwargs={
# 'pk': self.match.pk})
# ctx['kind'] = self.kind
# ctx['club'] = club
# if self.kind == 'goal':
# ctx['title'] = 'Goal: Select player'
# ctx['players'] = Squad.get_squad(
# self.match, club).get_playing_players()
# ctx['attrs'] = GoalAttr.objects.all()
# elif self.kind == 'own':
# opclub = self.match.get_opponent_club(club)
# ctx['title'] = 'Goal(own): Select player'
# ctx['players'] = Squad.get_squad(
# self.match, opclub).get_playing_players()
# elif self.kind == 'yellow':
# ctx['title'] = 'Yellow card: Select player'
# ctx['players'] = Squad.get_squad(
# self.match, club).get_playing_players()
# ctx['attrs'] = CardReason.objects.all()
# elif self.kind == 'red':
# ctx['title'] = 'Red card: Select player'
# ctx['players'] = Squad.get_squad(
# self.match, club).get_playing_players()
# ctx['attrs'] = CardReason.objects.all()
# return ctx

class PlayerSelect(LoginRequiredMixin,
                   formviewMixins,
                   MatchLockMixin,
                   FormView):

    template_name = 'dashboard/match/player_select.html'
    kind = 'goal'

    def get_context_data(self, **kwargs):
        club_pk = kwargs.get('club')
        club = get_object_or_404(ClubProfile, pk=club_pk)
        ctx = super().get_context_data(**kwargs)
        ctx['backurl'] = reverse('dash:enterpastmatchdetails', kwargs={
                                 'pk': self.match.pk})
        ctx['kind'] = self.kind
        ctx['club'] = club
        if self.kind == 'goal':
            ctx['title'] = 'Goal: Select player'
            ctx['players'] = Squad.get_squad(
                self.match, club).get_playing_players()
            ctx['attrs'] = GoalAttr.objects.all()
        elif self.kind == 'own':
            opclub = self.match.get_opponent_club(club)
            ctx['title'] = 'Goal(own): Select player'
            ctx['players'] = Squad.get_squad(
                self.match, opclub).get_playing_players()
        elif self.kind == 'yellow':
            ctx['title'] = 'Yellow card: Select player'
            ctx['players'] = Squad.get_squad(
                self.match, club).get_playing_players()
            ctx['attrs'] = CardReason.objects.all()
        elif self.kind == 'red':
            ctx['title'] = 'Red card: Select player'
            ctx['players'] = Squad.get_squad(
                self.match, club).get_playing_players()
            ctx['attrs'] = CardReason.objects.all()
        return ctx

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.kind == 'goal':
            kwargs['qplayers'] = Squad.get_squad(
                self.match, club).get_playing_players()
            kwargs['qattrs'] = GoalAttr.objects.all()
        elif self.kind == 'own':
            opclub = self.match.get_opponent_club(club)
            kwargs['qplayers'] = Squad.get_squad(
                self.match, opclub).get_playing_players()
        elif self.kind == 'yellow':
            kwargs['qplayers'] = Squad.get_squad(
                self.match, club).get_playing_players()
            kwargs['qattrs'] = CardReason.objects.all()
        elif self.kind == 'red':
            kwargs['qplayers'] = Squad.get_squad(
                self.match, club).get_playing_players()
            kwargs['qattrs'] = CardReason.objects.all()
        return kwargs


urlpatterns += [path('goalplayersel/<int:pk>/<int:club>/',
                     PlayerSelect.as_view(kind='goal'),
                     name='goalplayersel'), ]
urlpatterns += [path('ownplayersel/<int:pk>/<int:club>/',
                     PlayerSelect.as_view(kind='own'),
                     name='ownplayersel'), ]
urlpatterns += [path('yellowplayersel/<int:pk>/<int:club>/',
                     PlayerSelect.as_view(kind='yellow'),
                     name='yellowplayersel'), ]
urlpatterns += [path('redplayersel/<int:pk>/<int:club>/',
                     PlayerSelect.as_view(kind='red'),
                     name='redplayersel'), ]
