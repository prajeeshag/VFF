
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

from . import models
from . import forms
from django.contrib.auth.decorators import user_passes_test


class Home(LoginRequiredMixin, TemplateView):
    template_name = 'users/home.html'
    login_url = reverse_lazy('login')

    def get(self, request, *args, **kwargs):
        user = request.user
        if user.is_club():
            return redirect(reverse('users:clublist'))

        if user.is_player() and not hasattr(user, 'playerprofile'):
            return redirect(reverse('create_player_profile'))

        return super().get(request, *args, **kwargs)


class UsersList(LoginRequiredMixin, ListView):
    model = get_user_model()
    login_url = reverse_lazy('login')
    template_name = 'users/users_list.html'

    def get(self, request, *args, **kwargs):
        if not request.user.is_staff:
            return HttpResponseForbidden()
        return super().get(request, *args, **kwargs)


class FreePlayersList(LoginRequiredMixin, TemplateView):
    template_name = 'users/free_players_list.html'
    login_url = reverse_lazy('login')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # very bad, need improvement
        allplayers = models.PlayerProfile.objects.all()
        free_players = []
        for player in allplayers:
            if not player.get_club():
                free_players.append(player)
        ctx['free_players'] = free_players
        user = self.request.user
        if hasattr(user, 'clubprofile'):
            ctx['myoffers'] = user.clubprofile.get_invited_players()
            ctx['myplayers'] = user.clubprofile.get_players()
        return ctx


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
        user = self.request.user
        if hasattr(user, 'clubprofile'):
            ctx['myoffers'] = user.clubprofile.get_invited_players()
            ctx['myplayers'] = user.clubprofile.get_players()
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
    form_class = forms.UpdateClubForm
    login_url = reverse_lazy('login')
    template_name = 'users/base_form.html'
    success_message = 'Club details has been updated'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_club:
            return HttpResponseForbidden()
        return super().dispatch(request, *args, **kwargs)

    def get_object(self):
        return self.request.user.get_club()


class ClubOfficialsProfileUpdate(LoginRequiredMixin, SuccessMessageMixin,
                                 RedirectToPreviousMixin, UpdateView):
    model = models.ClubOfficialsProfile
    form_class = forms.UpdateClubOfficialsForm
    template_name = 'users/base_form.html'

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


@require_http_methods(['POST'])
@login_required
def CreateClubSigninOffer(request, pk):

    url = request.META.get('HTTP_REFERER', "/")

    try:
        player = models.PlayerProfile.objects.get(pk=pk)
    except:
        messages.add_message(
            request, messages.WARNING,
            _("Couldn't create signing offer."))
        return HttpResponseRedirect(url)

    club = getattr(request.user, 'clubprofile', None)
    if not club:
        messages.add_message(
            request, messages.WARNING,
            _("You are not authorised to create a signing offer."))
        return HttpResponseRedirect(url)

    signin, created = models.ClubSignings.objects.get_or_create(
        club=club, player=player)

    if not created:
        messages.add_message(
            request, messages.INFO,
            "Your have already sent an offer to {}".format(player))
    else:
        messages.add_message(
            request, messages.SUCCESS,
            "Created an offer for {}".format(player))

    return HttpResponseRedirect(url)


@require_http_methods(['POST'])
@login_required
def CancelClubSigninOffer(request, pk):
    url = request.META.get('HTTP_REFERER', "/")
    try:
        player = models.PlayerProfile.objects.get(pk=pk)
    except:
        messages.add_message(
            request, messages.WARNING,
            _("Couldn't cancel signing offer."))
        return HttpResponseRedirect(url)

    club = getattr(request.user, 'clubprofile', None)
    if not club:
        messages.add_message(
            request, messages.WARNING,
            _("You are not authorised to cancel a signing offer."))
        return HttpResponseRedirect(url)

    signin, created = models.ClubSignings.objects.get_or_create(
        club=club, player=player)

    if signin.accepted:
        messages.add_message(
            request, messages.WARNING,
            "Cannot cancel an accepted offer")
    else:
        signin.delete()

    return HttpResponseRedirect(url)


class PasswordChange(SuccessMessageMixin,
                     LoginRequiredMixin,
                     PasswordChangeView):
    template_name = 'users/base_form.html'
    success_message = 'Password Changed...'
    success_url = reverse_lazy('dash:home')
    extra_context = {'title': "Change Password"}


class UpdatePlayerProfile(SuccessMessageMixin,
                          LoginRequiredMixin,
                          UpdateView):
    model = models.PlayerProfile
    fields = ['first_name', 'last_name', 'dob',
              'address', 'pincode', 'student',
              'occupation', 'prefered_foot',
              'favorite_position', 'height',
              'weight']
    template_name = 'users/base_form.html'
    login_url = reverse_lazy('login')
    success_message = 'Profile updated'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_player():
            return HttpResponseForbidden()
        return super().dispatch(request, *args, **kwargs)

    def get_object(self):
        return self.request.user.get_profile()


class dpUploadView(LoginRequiredMixin, UpdateView):
    model = models.ProfilePicture
    form_class = forms.dpUploadForm
    template_name = 'users/dp_upload.html'

    def get_success_url(self):
        return reverse('users:dpedit')

    def get_object(self):
        return self.request.user.get_profilepicture()


class dpEditView(LoginRequiredMixin, UpdateView):
    form_class = forms.dpEditForm
    template_name = 'users/dp_edit.html'

    def get_object(self):
        return self.request.user.get_profilepicture()

    def get_success_url(self):
        return self.request.user.get_profile().get_absolute_url()


@ require_http_methods(['POST'])
@ login_required
def AcceptClubSigninOffer(request, pk):
    url = request.META.get('HTTP_REFERER', "/")

    try:
        signin = models.ClubSignings.objects.get(pk=pk)
    except models.ClubSignings.DoesNotExist:
        messages.add_message(
            request, messages.WARNING,
            "Cannot not accept signin offer, signin offer not found")
        return HttpResponseRedirect(url)

    if signin.player != request.user.get_profile():
        messages.add_message(
            request, messages.WARNING,
            "You are not authorised to accept this  offer")
        return HttpResponseRedirect(url)

    if signin.accepted:
        messages.add_message(
            request, messages.WARNING,
            "Already accepted this offer")
        return HttpResponseRedirect(url)

    try:
        signin.accept()
    except signin.MaximumLimitReached:
        messages.add_message(
            request, messages.WARNING,
            "Cannot accept this offer, the club reached maximum limit of players")
        return HttpResponseRedirect(url)
    except signin.AcceptedOfferExist:
        messages.add_message(
            request, messages.WARNING,
            "Cannot accept this offer, you already joined a club.")
        return HttpResponseRedirect(url)

    messages.add_message(
        request, messages.WARNING,
        "Congratulations!!, you are now a player of {}".format(signin.club))

    return HttpResponseRedirect(url)


@ require_http_methods(['POST'])
@ login_required
def RegectClubSigninOffer(request, pk):
    url = request.META.get('HTTP_REFERER', "/")

    try:
        signin = models.ClubSignings.objects.get(pk=pk)
    except models.ClubSignings.DoesNotExist:
        messages.add_message(
            request, messages.WARNING,
            "Cannot not regect signin offer, signin offer not found")
        return HttpResponseRedirect(url)

    if signin.player != request.user.get_profile():
        messages.add_message(
            request, messages.WARNING,
            "You are not authorised to regect this  offer")
        return HttpResponseRedirect(url)

    if signin.accepted:
        messages.add_message(
            request, messages.WARNING,
            "Cannot reject accepted offer")
        return HttpResponseRedirect(url)

    signin.delete()

    messages.add_message(
        request, messages.WARNING,
        "You regected an offer from {}".format(signin.club))

    return HttpResponseRedirect(url)
