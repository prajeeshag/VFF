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

LOGIN_URL = reverse_lazy('login')

urlpatterns = []


class AddFirstTeam(LoginRequiredMixin, viewMixins, View):
    template_name = 'dashboard/match/add_first_team.html'

    def dispatch(self, request, *arg, **kwargs):
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

        self.squad = squad
        self.user = user
        self.club = club
        self.match = match
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *arg, **kwargs):
        ctx = self.get_context_data(self, **kwargs)
        ctx['first_team_players'] = self.squad.get_first_team_player()
        ctx['available_players'] = self.squad.get_available_players()
        return render(request, self.template_name, ctx)

    def post(self, request, *args, **kwargs):
        obj_pks_fix = request.POST.getlist('checksFix')
        obj_pks_unfix = request.POST.getlist('checksUnFix')
        if obj_pks_fix:
            Matches.objects.filter(pk__in=obj_pks_fix).update(
                status=Matches.FIXED)
        if obj_pks_unfix:
            Matches.objects.filter(pk__in=obj_pks_unfix).update(
                status=Matches.TENTATIVE)

        ctx = self.get_context_data(self, **kwargs)
        ctx['first_team_players'] = self.squad.get_first_team_player()
        ctx['available_players'] = self.squad.get_available_players()
        return render(request, self.template_name, ctx)


urlpatterns += [path('fixmatches/',
                     fixMatches.as_view(),
                     name='fixmatches'), ]
