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

import rules
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
from match.models import (Squad, MatchTimeLine, Goal, Cards,
                          GoalAttr, CardReason, SubstitutionReason)
from users.models import PlayerProfile, ClubProfile
from .forms import (
    DateTimeForm, MatchTimeForm, EmptyForm,
    PlayerSelectForm, PlayerSelectForm2,
    PlayerSelectFormOnspot, PlayerSelectForm2Onspot,
)

LOGIN_URL = reverse_lazy('login')

urlpatterns = []


class ManageMatchList(LoginRequiredMixin, viewMixins, TemplateView):
    template_name = 'dashboard/match/manage_match_list.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['matches'] = Matches.objects.exclude(
            status=Matches.STATUS.done).order_by('date')
        return ctx


urlpatterns += [path('managematches/',
                     ManageMatchList.as_view(),
                     name='managematches'), ]


class EnterPastMatchDetails(LoginRequiredMixin, viewMixins, DetailView):
    template_name = 'dashboard/match/enter_match_details.html'
    model = Matches
    context_object_name = 'match'

    def get(self, request, *args, **kwargs):
        match = self.get_object()
        self.match = match
        if request.session.get('onspot_'+str(match.pk), None) is None:
            request.session['onspot_'+str(match.pk)] = True
        if match.is_tentative():
            messages.add_message(
                request, messages.WARNING,
                "Cannot Enter match details. This match is tentative!")
            return redirect(self.backurl)
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['onspot'] = self.request.session.get('onspot_'+str(self.match.pk))
        return ctx


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

        is_match_manager = rules.test_rule('manage_match', request.user)
        if not squad.is_pre() and not is_match_manager:
            messages.add_message(
                request, messages.INFO,
                "Squad Finalized")
            return redirect(squad)

        self.squad = squad
        self.user = user
        self.club = club
        self.match = match
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *arg, **kwargs):
        ctx = self.get_context_data(**kwargs)
        ctx['squad'] = self.squad.get_first_squad()
        ctx['squad_av'] = self.squad.get_avail_squad()
        ctx['stepnexturl'] = reverse('dash:addsubteam', kwargs={
            'club': self.club.pk,
            'match': self.match.pk})
        ctx['club'] = self.club
        ctx['match'] = self.match
        request.session['add_squad_return_url'] = request.session.get(
            'previous_page', None)
        return render(request, self.template_name, ctx)

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action')
        pk = request.POST.get('pk', None)

        if action == 'add':
            player = get_object_or_404(PlayerProfile, pk=pk)
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
            player = get_object_or_404(PlayerProfile, pk=pk)
            self.squad.remove_player_from_first(player)
        elif action == 'reset':
            self.squad.reset()
        elif action == 'hardreset':
            try:
                self.squad.items.all().delete()
                self.squad.delete()
                Squad.create(self.match, self.club, user=request.user)
            except Exception as e:
                messages.add_message(
                    request, messages.WARNING, e)

        return redirect(self.backurl)


urlpatterns += [path('addfirstteam/<int:match>/<int:club>/',
                     AddFirstTeam.as_view(),
                     name='addfirstteam'), ]


class AddSubTeam(AddFirstTeam):
    template_name = 'dashboard/match/add_team.html'

    def get(self, request, *arg, **kwargs):
        ctx = self.get_context_data(**kwargs)
        ctx['squad'] = self.squad.get_bench_squad()
        ctx['squad_av'] = self.squad.get_avail_squad()
        ctx['stepnexturl'] = reverse('dash:finalizesquad', kwargs={
            'club': self.club.pk,
            'match': self.match.pk})
        ctx['stepbackurl'] = reverse('dash:addfirstteam', kwargs={
            'club': self.club.pk,
            'match': self.match.pk})
        ctx['club'] = self.club
        ctx['match'] = self.match
        return render(request, self.template_name, ctx)

    def post(self, request, *args, **kwargs):
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
        ctx = self.get_context_data(**kwargs)
        ctx['squad'] = self.squad.get_first_squad()
        ctx['squad_av'] = self.squad.get_bench_squad()
        ctx['stepbackurl'] = reverse('dash:addsubteam', kwargs={
            'club': self.club.pk,
            'match': self.match.pk})
        ctx['club'] = self.club
        ctx['match'] = self.match
        return render(request, self.template_name, ctx)

    def post(self, request, *args, **kwargs):
        try:
            self.squad.finalize()
        except self.squad.NotEnoughPlayers as e:
            messages.add_message(request, messages.WARNING, e)
            return redirect(self.backurl)

        if rules.test_rule('manage_match', self.request.user):
            return redirect(reverse('dash:enterpastmatchdetails',
                                    kwargs={'pk': self.match.pk}))
        else:
            return redirect(self.squad)


urlpatterns += [path('finalizesquad/<int:match>/<int:club>/',
                     FinalizeSquad.as_view(),
                     name='finalizesquad'), ]


class MatchLockMixin:
    def dispatch(self, request, *args, **kwargs):
        pk = kwargs.get('pk')
        match = get_object_or_404(Matches, pk=pk)
        self.match = match
        return super().dispatch(request, *args, **kwargs)


class StartMatchTimeLine(LoginRequiredMixin,
                         MatchLockMixin,
                         View):
    model = Matches

    def get_success_url(self):
        return reverse('dash:enterpastmatchdetails', kwargs={'pk': self.get_object().pk})

    def post(self, request, *args, **kwargs):
        pk = kwargs.get('pk')
        match = get_object_or_404(Matches, pk=pk)
        for club in [match.home, match.away]:
            try:
                obj = Squad.objects.get(match=match, club=club)
            except Squad.DoesNotExist:
                Squad.create(match, club, request.user)
        return redirect(reverse('dash:enterpastmatchdetails', kwargs={'pk': match.pk}))


urlpatterns += [path('startmatchtimeline/<int:pk>/',
                     StartMatchTimeLine.as_view(),
                     name='startmatchtimeline'), ]


class ActivatePast(LoginRequiredMixin, MatchLockMixin, View):

    def post(self, request, *args, **kwargs):
        val = request.POST.get('action')
        if val == 'onspot':
            request.session['onspot_'+str(self.match.pk)] = True
        elif val == 'past':
            request.session['onspot_'+str(self.match.pk)] = False
        return redirect(reverse('dash:enterpastmatchdetails', kwargs={'pk': self.match.pk}))


urlpatterns += [path('activatepast/<int:pk>/',
                     ActivatePast.as_view(),
                     name='activatepast'), ]


class TimeEvent(LoginRequiredMixin,
                formviewMixins,
                MatchLockMixin,
                FormView):
    form_class = DateTimeForm
    template_name = 'dashboard/match/base_form.html'
    onspot = False
    kind = 'start'

    def get_form_class(self):
        if self.onspot:
            return EmptyForm
        return DateTimeForm

    def get_success_url(self):
        return reverse('dash:enterpastmatchdetails', kwargs={'pk': self.match.pk})

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.kind == 'start':
            ctx['title'] = 'Start Match'
        elif self.kind == 'halftime':
            ctx['title'] = 'Half Time'
        elif self.kind == 'secondhalf':
            ctx['title'] = 'Second Half'
        elif self.kind == 'fulltime':
            ctx['title'] = 'Full time'
        ctx['return_url'] = reverse(
            'dash:enterpastmatchdetails',
            kwargs={'pk': self.match.pk})
        return ctx

    def get_initial(self):
        timeline = getattr(self.match, 'matchtimeline', None)
        if timeline and timeline.first_half_start:
            return {'time': timeline.first_half_start}
        return {'time': self.match.date}

    def form_valid(self, form):
        time = form.cleaned_data.get('time', None)

        if self.kind == 'start':
            if self.match.matchtimeline.first_half_start:
                messages.add_message(
                    self.request, messages.DANGER,
                    "Match already started!!")
            else:
                self.match.matchtimeline.start_match(time=time)
        elif self.kind == 'halftime':
            if self.match.matchtimeline.half_time:
                messages.add_message(
                    self.request, messages.DANGER,
                    "Match already in half time!!")
            else:
                self.match.matchtimeline.set_half_time(time=time)
        elif self.kind == 'secondhalf':
            if self.match.matchtimeline.second_half_start:
                messages.add_message(
                    self.request, messages.DANGER,
                    "Second half already started!!")
            else:
                self.match.matchtimeline.start_second_half(time=time)
        elif self.kind == 'fulltime':
            if self.match.matchtimeline.final_time:
                messages.add_message(
                    self.request, messages.WARNING,
                    "Match already in Final Time!!")
            else:
                self.match.matchtimeline.finalize_match(time=time)

        return super().form_valid(form)


urlpatterns += [path('startmatch/<int:pk>/',
                     TimeEvent.as_view(kind='start'),
                     name='startmatch'), ]
urlpatterns += [path('startmatchonspot/<int:pk>/',
                     TimeEvent.as_view(kind='start', onspot=True),
                     name='startmatchonspot'), ]
urlpatterns += [path('halftime/<int:pk>/',
                     TimeEvent.as_view(kind='halftime'),
                     name='halftime'), ]
urlpatterns += [path('halftimeonspot/<int:pk>/',
                     TimeEvent.as_view(kind='halftime', onspot=True),
                     name='halftimeonspot'), ]
urlpatterns += [path('secondhalf/<int:pk>/',
                     TimeEvent.as_view(kind='secondhalf'),
                     name='secondhalf'), ]
urlpatterns += [path('secondhalfonspot/<int:pk>/',
                     TimeEvent.as_view(kind='secondhalf', onspot=True),
                     name='secondhalfonspot'), ]
urlpatterns += [path('finaltime/<int:pk>/',
                     TimeEvent.as_view(kind='fulltime'),
                     name='finaltime'), ]
urlpatterns += [path('finaltimeonspot/<int:pk>/',
                     TimeEvent.as_view(kind='fulltime', onspot=True),
                     name='finaltimeonspot'), ]


class PlayerSelect(LoginRequiredMixin,
                   formviewMixins,
                   MatchLockMixin,
                   FormView):
    form_class = PlayerSelectForm
    template_name = 'dashboard/match/player_select.html'
    kind = 'goal'
    onspot = False

    def get_form_class(self):
        if self.onspot:
            return PlayerSelectFormOnspot
        else:
            return PlayerSelectForm

    def get_initial(self):
        timeline = getattr(self.match, 'matchtimeline', None)
        if timeline and timeline.first_half_start:
            return {'time': timeline.first_half_start}
        return {'time': self.match.date}

    def get_success_url(self):
        return reverse('dash:enterpastmatchdetails', kwargs={'pk': self.match.pk})

    def dispatch(self, request, *args, **kwargs):
        club_pk = kwargs.get('club')
        self.club = get_object_or_404(ClubProfile, pk=club_pk)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        club = self.club
        ctx = super().get_context_data(**kwargs)
        ctx['backurl'] = reverse('dash:enterpastmatchdetails', kwargs={
                                 'pk': self.match.pk})
        ctx['kind'] = self.kind
        ctx['club'] = club
        if self.kind == 'goal':
            ctx['title'] = 'Goal'
        elif self.kind == 'own':
            ctx['title'] = 'Goal(Own)'
        elif self.kind == 'yellow':
            ctx['title'] = 'Yellow Card'
        elif self.kind == 'red':
            ctx['title'] = 'Red Card'
        return ctx

    def get_form_kwargs(self):
        club = self.club
        kwargs = super().get_form_kwargs()
        if self.kind == 'goal':
            kwargs['qplayers'] = Squad.get_squad(
                self.match, club).get_playing_players()
            kwargs['qattrs'] = GoalAttr.objects.exclude(text='own goal')
            kwargs['attr_required'] = False
        elif self.kind == 'own':
            opclub = self.match.get_opponent_club(club)
            kwargs['qplayers'] = Squad.get_squad(
                self.match, opclub).get_playing_players()
            kwargs['qattrs'] = ['own goal']
            kwargs['attr_required'] = False
        elif self.kind == 'yellow':
            kwargs['qplayers'] = Squad.get_squad(
                self.match, club).get_playing_players()
            kwargs['qattrs'] = CardReason.objects.all()
        elif self.kind == 'red':
            kwargs['qplayers'] = Squad.get_squad(
                self.match, club).get_playing_players()
            kwargs['qattrs'] = CardReason.objects.all()
        return kwargs

    def form_valid(self, form):
        player = form.cleaned_data.get('player')
        attr = form.cleaned_data.get('attr')
        time = form.cleaned_data.get('time', None)
        if attr == 'None':
            attr = None

        if self.kind == 'goal':
            Goal.create(match=self.match, player=player,
                        created_by=self.request.user, time=time,
                        attr=attr)
        elif self.kind == 'own':
            attr = 'own goal'
            Goal.create(match=self.match, player=player,
                        created_by=self.request.user, time=time,
                        attr=attr, own=True)
        elif self.kind == 'yellow':
            Cards.raise_yellow_card(
                match=self.match, player=player,
                reason_text=attr, time=time)
        elif self.kind == 'red':
            Cards.raise_red_card(
                match=self.match, player=player,
                reason_text=attr, time=time)

        return super().form_valid(form)


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
urlpatterns += [path('goalplayerselonspot/<int:pk>/<int:club>/',
                     PlayerSelect.as_view(kind='goal', onspot=True),
                     name='goalplayerselonspot'), ]
urlpatterns += [path('ownplayerselonspot/<int:pk>/<int:club>/',
                     PlayerSelect.as_view(kind='own', onspot=True),
                     name='ownplayerselonspot'), ]
urlpatterns += [path('yellowplayerselonspot/<int:pk>/<int:club>/',
                     PlayerSelect.as_view(kind='yellow', onspot=True),
                     name='yellowplayerselonspot'), ]
urlpatterns += [path('redplayerselonspot/<int:pk>/<int:club>/',
                     PlayerSelect.as_view(kind='red', onspot=True),
                     name='redplayerselonspot'), ]


class PlayerSelect2(LoginRequiredMixin,
                    formviewMixins,
                    MatchLockMixin,
                    FormView):
    form_class = PlayerSelectForm2
    template_name = 'dashboard/match/player_select.html'
    onspot = False

    def get_initial(self):
        timeline = getattr(self.match, 'matchtimeline', None)
        if timeline and timeline.first_half_start:
            return {'time': timeline.first_half_start}
        return {'time': self.match.date}

    def get_form_class(self):
        if self.onspot:
            return PlayerSelectForm2Onspot
        return PlayerSelectForm2

    def get_success_url(self):
        return reverse('dash:enterpastmatchdetails', kwargs={'pk': self.match.pk})

    def dispatch(self, request, *args, **kwargs):
        club_pk = kwargs.get('club')
        self.club = get_object_or_404(ClubProfile, pk=club_pk)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        club = self.club
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Substitution'
        ctx['backurl'] = reverse('dash:enterpastmatchdetails', kwargs={
                                 'pk': self.match.pk})
        ctx['club'] = club
        return ctx

    def get_form_kwargs(self):
        club = self.club
        kwargs = super().get_form_kwargs()
        kwargs['qplayers_out'] = Squad.get_squad(
            self.match, club).get_playing_players()
        kwargs['qplayers_in'] = Squad.get_squad(
            self.match, club).get_onbench_players()
        kwargs['qattrs'] = SubstitutionReason.objects.all()
        return kwargs

    def form_valid(self, form):
        player_in = form.cleaned_data.get('player_in')
        player_out = form.cleaned_data.get('player_out')
        attr = form.cleaned_data.get('attr')
        time = form.cleaned_data.get('time', None)
        if attr == 'None':
            attr = None

        squad = Squad.get_squad(match=self.match, club=self.club)

        try:
            squad.substitute(playerin=player_in,
                             playerout=player_out, user=self.request.user,
                             time=time,  reason_text=attr)
        except squad.NotEnoughPlayers as e:
            messages.add_message(self.request, messages.WARNING, e)
            return self.form_invalid(form)

        return super().form_valid(form)


urlpatterns += [path('subplayersel/<int:pk>/<int:club>/',
                     PlayerSelect2.as_view(),
                     name='subplayersel'), ]

urlpatterns += [path('subplayerselonspot/<int:pk>/<int:club>/',
                     PlayerSelect2.as_view(onspot=True),
                     name='subplayerselonspot'), ]
