from django.db.models import Count, Q

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
import rules

from extra_views import UpdateWithInlinesView, InlineFormSetFactory, ModelFormSetView

from core.mixins import formviewMixins, viewMixins
from formtools.wizard.views import SessionWizardView

from fixture.models import Matches
from users.models import PlayerProfile, PhoneNumber, Document, ClubProfile
from league.models import Season
from verification.models import Verification

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

        if user.is_player() and not club:
            profile = user.get_profile()
            if profile:
                ctx['club_offers'] = profile.get_all_offers()

        if user.is_club():
            if Season.objects.first().is_transfer_window_open():
                ctx['player_quota'] = club.player_quota_left()

        is_match_manager = rules.test_rule('manage_match', self.request.user)
        if is_match_manager:
            num_players = Count('players')
            num_noacc_players = Count('players', filter=Q(players__user=None))
            num_unverified_players = Count('players', filter=~Q(
                players__verification__status='VERIFIED'))
            clubInfo = ClubProfile.objects.annotate(
                num_players=num_players,
                num_noacc_players=num_noacc_players,
                num_unverified_players=num_unverified_players,
            )
            ctx['clubInfo'] = clubInfo

        return ctx


urlpatterns += [path('home/', Home.as_view(), name='home'), ]


class Calendar(viewMixins, TemplateView):
    template_name = 'dashboard/calendar.html'
    login_url = LOGIN_URL

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['matches'] = Matches.get_upcoming_matches()
        ctx['done_matches'] = Matches.objects.filter(
            status=Matches.STATUS.done).order_by('-date')
        return ctx


urlpatterns += [path('calendar/', Calendar.as_view(), name='calendar'), ]


class documentEditView(LoginRequiredMixin, formviewMixins, FormView):
    form_class = forms.imageEditForm
    template_name = 'dashboard/image_edit.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['instance'] = get_object_or_404(
            Document, pk=self.kwargs.get('pk', None)
        )
        return kwargs

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)


urlpatterns += [path('documentedit/<int:pk>/',
                     documentEditView.as_view(),
                     name='documentedit'), ]


class documentUploadView(LoginRequiredMixin, formviewMixins, UpdateView):
    model = Document
    fields = ['image', ]
    template_name = 'dashboard/image_upload.html'

    def get_success_url(self):
        redirect_url = self.request.POST.get('redirect_url', None)
        if redirect_url:
            return redirect_url

        return reverse('dash:documentedit', kwargs={
                       'pk': self.kwargs.get('pk')})


urlpatterns += [path('documentupload/<int:pk>/',
                     documentUploadView.as_view(),
                     name='documentupload'), ]
