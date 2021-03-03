
from django.db.models import Count, ProtectedError
from django.db import transaction
from django import forms as dj_forms

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
from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied

from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.contrib.auth import get_user_model
from django.shortcuts import redirect, render, get_object_or_404
from django.views.decorators.http import require_http_methods

from extra_views import UpdateWithInlinesView, InlineFormSetFactory, ModelFormSetView
import rules

from core.mixins import viewMixins, formviewMixins
from formtools.wizard.views import SessionWizardView
from formtools.preview import FormPreview

from . import models
from . import forms
from league.models import Season
from league.views import ProfileManagerRequiredMixin

urlpatterns = []


class UsersList(LoginRequiredMixin, viewMixins, ListView):
    model = get_user_model()
    login_url = reverse_lazy('login')
    template_name = 'users/users_list.html'

    def get(self, request, *args, **kwargs):
        if not request.user.is_staff:
            return HttpResponseForbidden()
        return super().get(request, *args, **kwargs)


urlpatterns += [path('userlist/', UsersList.as_view(), name='list'), ]


class FreePlayersList(LoginRequiredMixin, viewMixins, TemplateView):
    template_name = 'users/free_players_list.html'
    login_url = reverse_lazy('login')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        allplayers = models.PlayerProfile.objects.exclude(
            user=None).filter(club=None)
        ctx['free_players'] = allplayers
        user = self.request.user
        ctx['send_offer'] = True
        if hasattr(user, 'clubprofile'):
            ctx['myoffers'] = user.clubprofile.get_invited_players()
            ctx['myplayers'] = user.clubprofile.get_players()
        return ctx


urlpatterns += [path('unsignedplayers/',
                     FreePlayersList.as_view(),
                     name='unsignedplayers'), ]


class AllPlayers(ProfileManagerRequiredMixin, TemplateView):
    template_name = 'users/all_players.html'
    model = models.PlayerProfile

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        value_list = models.PlayerProfile.objects.values(
            'dob').annotate(num=Count('dob')).order_by('-num')
        group_by_value = {}
        for value in value_list:
            group_by_value[value['dob']] = models.PlayerProfile.objects.filter(
                dob=value['dob'])
        ctx['groupbydob'] = group_by_value
        return ctx


urlpatterns += [path('allplayers/',
                     AllPlayers.as_view(),
                     name='allplayers'), ]


class ReleasePlayer(FormView):
    template_name = 'dashboard/base_form.html'
    form_class = dj_forms.Form

    def dispatch(self, request, *args, **kwargs):
        user = request.user
        self.club = user.get_club()
        is_club_manager = rules.test_rule('manage_club', user, self.club)
        if not is_club_manager:
            raise PermissionDenied

        pk = kwargs.get('pk')
        self.player = get_object_or_404(models.PlayerProfile, pk=pk)
        if not self.player.club or self.player.club != self.club:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.club.release_player(self.player)
        self.player.refresh_from_db()
        if not self.player.club and not self.player.user:
            try:
                self.player.delete()
            except Exception:
                pass

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Are you sure you want to remove {} from your club?'.format(
            self.player)
        ctx['back_url'] = self.club.get_absolute_url()
        return ctx

    def get_success_url(self):
        return(self.club.get_absolute_url())


urlpatterns += [path('releaseplayer/<int:pk>/',
                     ReleasePlayer.as_view(),
                     name='releaseplayer'), ]


class CreateEndContract(FormView):
    template_name = 'dashboard/base_form.html'
    form_class = dj_forms.Form

    def dispatch(self, request, *args, **kwargs):
        user = request.user
        self.club = user.get_club()
        is_club_manager = rules.test_rule('manage_club', user, self.club)
        if not is_club_manager:
            raise PermissionDenied
        pk = kwargs.get('pk')
        self.player = get_object_or_404(models.PlayerProfile, pk=pk)
        if not self.player.club or self.player.club != self.club:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        obj, created = models.EndContract.objects.get_or_create(
            club=self.club, player=self.player)
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Are you sure you want to sent a contract termination request to {}?'.format(
            self.player)
        ctx['back_url'] = self.club.get_absolute_url()
        return ctx

    def get_success_url(self):
        return(self.club.get_absolute_url())


urlpatterns += [path('createendcontract/<int:pk>/',
                     CreateEndContract.as_view(),
                     name='createendcontract'), ]


class DeleteEndContract(FormView):
    template_name = 'dashboard/base_form.html'
    form_class = dj_forms.Form

    def dispatch(self, request, *args, **kwargs):
        user = request.user
        self.club = user.get_club()
        is_club_manager = rules.test_rule('manage_club', user, self.club)
        if not is_club_manager:
            raise PermissionDenied
        pk = kwargs.get('pk')
        self.player = get_object_or_404(models.PlayerProfile, pk=pk)
        if not self.player.club or self.player.club != self.club:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        obj, created = models.EndContract.objects.get_or_create(
            club=self.club, player=self.player)
        obj.delete()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Are you sure you want to delete the contract termination request to {}?'.format(
            self.player)
        ctx['back_url'] = self.club.get_absolute_url()
        return ctx

    def get_success_url(self):
        return(self.club.get_absolute_url())


urlpatterns += [path('deleteendcontract/<int:pk>/',
                     DeleteEndContract.as_view(),
                     name='deleteendcontract'), ]


class AgreeEndContract(FormView):
    template_name = 'dashboard/base_form.html'
    form_class = dj_forms.Form
    disagree = False

    def dispatch(self, request, *args, **kwargs):
        user = request.user
        pk = kwargs.get('pk')
        self.object = get_object_or_404(models.EndContract, pk=pk)
        if self.object.player != user.get_profile():
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        if self.disagree:
            self.object.disagree()
            messages.add_message(
                self.request, messages.INFO,
                "You disagreed to end the contract with {} !!".format(self.object.club))
        else:
            self.object.agree()
            messages.add_message(
                self.request, messages.INFO,
                "You ended the contract with {}, you are now an unsigned player!!".format(self.object.club))
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.disagree:
            ctx['title'] = 'Are you sure you want disagree end contract request from {}?'.format(
                self.object.club)
        else:
            ctx['title'] = 'Are you sure you want to end the contract with {}?'.format(
                self.object.club)
        ctx['back_url'] = self.object.player.get_absolute_url()
        return ctx

    def get_success_url(self):
        return(self.object.player.get_absolute_url())


urlpatterns += [path('agreeendcontract/<int:pk>/',
                     AgreeEndContract.as_view(),
                     name='agreeendcontract'), ]

urlpatterns += [path('disagreeendcontract/<int:pk>/',
                     AgreeEndContract.as_view(disagree=True),
                     name='disagreeendcontract'), ]


class MergeProfiles(ProfileManagerRequiredMixin, FormView):
    template_name = 'dashboard/base_form.html'
    form_class = dj_forms.Form

    def dispatch(self, request, *args, **kwargs):
        pk1 = kwargs.get('pk1', None)
        pk2 = kwargs.get('pk2', None)
        self.profile1 = get_object_or_404(models.PlayerProfile, pk=pk1)
        self.profile2 = get_object_or_404(models.PlayerProfile, pk=pk2)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Are you sure you want to merge {} & {}?'.format(
            self.profile1, self.profile2)
        ctx['back_url'] = reverse('users:allplayers')
        return ctx

    def form_valid(self, form):
        if self.profile1.user and self.profile2.user:
            messages.add_message(
                request, messages.WARNING,
                "Both profiles has users, cannot merge profiles!!")
        elif self.profile1.user:
            with transaction.atomic():
                self.profile2.user = self.profile1.user
                self.profile1.user = None
                self.profile1.save()
                self.profile2.save()
                self.profile1.delete()
        elif self.profile2.user:
            with transaction.atomic():
                self.profile1.user = self.profile2.user
                self.profile2.user = None
                self.profile2.save()
                self.profile1.save()
                self.profile2.delete()
        else:
            messages.add_message(
                request, messages.WARNING,
                "Both profiles has no users, cannot merge profiles!!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('users:allplayers')


urlpatterns += [path('mergeprofile/<int:pk1>/<int:pk2>/',
                     MergeProfiles.as_view(),
                     name='mergeprofiles'), ]


class DeleteProfile(ProfileManagerRequiredMixin, DeleteView):
    template_name = 'dashboard/base_form.html'
    model = models.PlayerProfile

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = "Are you sure you want to delete {}'s ?".format(
            self.object)
        ctx['back_url'] = reverse('users:allplayers')
        return ctx

    def post(self, request, *args, **kwargs):
        try:
            return self.delete(request, *args, **kwargs)
        except ProtectedError:
            messages.add_message(
                request, messages.WARNING,
                "Cannot delete this profile, this profile is protect from deletion by other objects!!")
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse('users:allplayers')


urlpatterns += [path('deleteprofile/<int:pk>/',
                     DeleteProfile.as_view(),
                     name='deleteprofile'), ]


class ClubList(viewMixins, TemplateView):
    template_name = 'dashboard/club_list.html'
    login_url = reverse_lazy('login')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['clubs'] = models.ClubProfile.objects.filter(user__is_active=True)
        return ctx


urlpatterns += [path('clublist/',
                     ClubList.as_view(),
                     name='clublist'), ]


class ClubMembersList(LoginRequiredMixin, viewMixins, DetailView):
    model = models.ClubProfile
    template_name = 'users/club_members_list.html'
    login_url = reverse_lazy('login')


urlpatterns += [path('clubmemberslist/<int:pk>/',
                     ClubMembersList.as_view(),
                     name='clubmemberslist'), ]


class ClubDetails(viewMixins, DetailView):
    template_name = 'users/club_details.html'
    login_url = reverse_lazy('login')
    model = models.ClubProfile

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        return ctx


urlpatterns += [path('clubdetails/<int:pk>/',
                     ClubDetails.as_view(),
                     name='clubdetails'), ]


class ClubOfficialsProfile(LoginRequiredMixin, viewMixins, DetailView):
    template_name = 'users/club_officials_profile.html'
    login_url = reverse_lazy('login')
    model = models.ClubOfficialsProfile

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        return ctx


urlpatterns += [path('clubofficials/<int:pk>/',
                     ClubOfficialsProfile.as_view(),
                     name='clubofficialsprofile'), ]


class PlayersProfile(viewMixins, DetailView):
    template_name = 'users/players_profile.html'
    login_url = reverse_lazy('login')
    model = models.PlayerProfile

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        return ctx


urlpatterns += [path('players/<int:pk>/',
                     PlayersProfile.as_view(),
                     name='playersprofile'), ]


class UpdateClubProfile(LoginRequiredMixin, SuccessMessageMixin,
                        formviewMixins, UpdateView):
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


urlpatterns += [path('updateclub/',
                     UpdateClubProfile.as_view(),
                     name='updateclubprofile'), ]


class ClubOfficialsProfileUpdate(LoginRequiredMixin, SuccessMessageMixin,
                                 formviewMixins, UpdateView):
    model = models.ClubOfficialsProfile
    form_class = forms.UpdateClubOfficialsForm
    template_name = 'users/base_form.html'

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if (not self.request.user.is_staff and
                obj.club.user != self.request.user):
            return HttpResponseForbidden()
        return super().dispatch(request, *args, **kwargs)


urlpatterns += [path('cluboffileupdate/<int:pk>/',
                     ClubOfficialsProfileUpdate.as_view(),
                     name='updateclubofficialsprofile'), ]


class abbrUpdateView(LoginRequiredMixin, formviewMixins, UpdateView):
    model = models.ClubProfile
    fields = ['abbr', ]
    template_name = 'users/abbr_form.html'


@require_http_methods(['POST'])
@login_required
def CreateClubSigninOffer(request, pk):

    url = request.META.get('HTTP_REFERER', "/")

    if not Season.objects.first().is_transfer_window_open():
        messages.add_message(
            request, messages.WARNING,
            "Cannot not send signin offer, Transfer window is closed")
        return HttpResponseRedirect(url)

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


urlpatterns += [path('sendoffer/<int:pk>',
                     CreateClubSigninOffer,
                     name='signinoffer'), ]


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


urlpatterns += [path('canceloffer/<int:pk>',
                     CancelClubSigninOffer,
                     name='cancelsigninoffer'), ]


class PasswordChange(SuccessMessageMixin,
                     LoginRequiredMixin,
                     PasswordChangeView):
    template_name = 'users/base_form.html'
    success_message = 'Password Changed...'
    success_url = reverse_lazy('dash:home')
    extra_context = {'title': "Change Password"}


urlpatterns += [path('changepassword/',
                     PasswordChange.as_view(), name='change_password'), ]


class UpdatePlayerProfile(SuccessMessageMixin,
                          LoginRequiredMixin,
                          formviewMixins,
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


class dpUploadView(LoginRequiredMixin, formviewMixins, UpdateView):
    model = models.ProfilePicture
    form_class = forms.dpUploadForm
    template_name = 'users/dp_upload.html'

    def get_success_url(self):
        return reverse('users:dpedit')

    def get_object(self):
        return self.request.user.get_profilepicture()


urlpatterns += [path('dpupload/', dpUploadView.as_view(), name='dpupload'), ]


class dpEditView(LoginRequiredMixin, formviewMixins, UpdateView):
    form_class = forms.dpEditForm
    template_name = 'users/dp_edit.html'

    def get_success_url(self):
        profile = getattr(self.object, 'playerprofile', None)
        if not profile:
            profile = getattr(self.object, 'clubofficialsprofile', None)
        if not profile:
            return('/')
        return profile.get_absolute_url()


urlpatterns += [path('dpedit/<int:pk>/',
                     dpEditView.as_view(),
                     name='dpedit'), ]


@ require_http_methods(['POST'])
@ login_required
def AcceptClubSigninOffer(request, pk):
    url = request.META.get('HTTP_REFERER', "/")

    if not Season.objects.first().is_transfer_window_open():
        messages.add_message(
            request, messages.WARNING,
            "Cannot not accept signin offer, Transfer window is closed")
        return HttpResponseRedirect(url)

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


urlpatterns += [path('acceptoffer/<int:pk>',
                     AcceptClubSigninOffer,
                     name='acceptsigninoffer'), ]


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


urlpatterns += [path('regectoffer/<int:pk>',
                     RegectClubSigninOffer,
                     name='regectsigninoffer'), ]
