from django.utils.decorators import method_decorator
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.base import TemplateView
from django.views.generic.detail import DetailView
from django.urls import reverse_lazy, reverse
from django import forms
from django.template import loader
from django.utils.safestring import mark_safe
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.http import HttpResponseForbidden
from django.contrib.auth import get_user_model
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.tokens import default_token_generator

from django_email_verification import sendConfirm

from users.decorators import verified_email_required


from .forms import (
    SignUpFormClub, OfficialsCreationForm, PlayerCreationForm,
    ProfilePictureForm, AddressProofForm, AgeProofForm,
    SignUpFormPersonal, LinkPlayerForm,
)
from .models import (
    Officials, PlayerInfo, Club, ClubDetails, JerseyPicture,
    ProfilePicture, AddressProof, AgeProof, Invitations
)


@method_decorator(verified_email_required, name='dispatch')
class HomePageView(LoginRequiredMixin, TemplateView):
    template_name = 'registration/home.html'
    login_url = reverse_lazy('login')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.request.user.is_staff:
            ctx['clubs'] = Club.objects.all()
        elif self.request.user.is_club():
            ctx['jerseypictures'] = self.request.user.club.jerseypictures.all()
            ctx['clubdetails'] = self.request.user.club.clubdetails
            ctx['players'] = self.request.user.club.Officials.filter(
                role="Player")
            ctx['officials'] = self.request.user.club.Officials.exclude(
                role="Player")
        return ctx


@method_decorator(verified_email_required, name='dispatch')
class ClubListView(LoginRequiredMixin, TemplateView):
    template_name = 'registration/club_list.html'
    login_url = reverse_lazy('login')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['clubs'] = Club.objects.filter(user__is_active=True)
        return ctx


class SignUpViewClub(SuccessMessageMixin, CreateView):
    form_class = SignUpFormClub
    success_url = reverse_lazy('home')
    template_name = 'registration/signup.html'
    success_message = 'User has been created'

    def form_valid(self, form):
        user = form.save(commit=False)
        User = get_user_model()
        user.user_type = User.CLUB
        club_name = form.cleaned_data['club_name']
        address = form.cleaned_data['address']
        contact_number = form.cleaned_data['contact_number']
        user.save()
        club = Club.objects.create(user=user, club_name=club_name)
        ClubDetails.objects.create(
            club=club, address=address, contact_number=contact_number)
        return super().form_valid(form)


class SignUpViewPersonal(SuccessMessageMixin, CreateView):
    form_class = SignUpFormPersonal
    success_url = reverse_lazy('login')
    template_name = 'registration/signup.html'
    success_message = 'User has been created, Please login.'

    def form_valid(self, form):
        user = form.save(commit=False)
        User = get_user_model()
        user.user_type = User.PERSONAL
        user.verification_email_send = True
        user.save()
        sendConfirm(user)
        return super().form_valid(form)


@method_decorator(verified_email_required, name='dispatch')
class AddJersey(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = JerseyPicture
    fields = ['image']
    login_url = reverse_lazy('login')
    template_name = 'registration/officials_form.html'
    success_message = 'Jersey has been added'

    def form_valid(self, form):
        form.instance.user = self.request.user.club
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('home')


@method_decorator(verified_email_required, name='dispatch')
class DeleteJersey(LoginRequiredMixin, SuccessMessageMixin, DeleteView):
    model = JerseyPicture
    login_url = reverse_lazy('login')
    template_name = 'registration/officials_confirm_delete.html'
    success_message = 'Jersey has been deleted'

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.user.user != self.request.user:
            return HttpResponseForbidden()
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('home')


@method_decorator(verified_email_required, name='dispatch')
class UpdateJersey(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = JerseyPicture
    fields = ['image']
    login_url = reverse_lazy('login')
    template_name = 'registration/officials_form.html'
    success_message = 'Jersey has been updated'

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.user.user != self.request.user:
            return HttpResponseForbidden()
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('home')


@method_decorator(verified_email_required, name='dispatch')
class AddOfficials(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    login_url = reverse_lazy('login')
    form_class = OfficialsCreationForm
    template_name = 'registration/officials_form.html'
    success_message = 'Profile has been created'

    def get_form_class(self):
        if self.kwargs['role'] == 'Player':
            return PlayerCreationForm
        return OfficialsCreationForm

    def form_valid(self, form):
        form.instance.club = self.request.user.club
        user = form.save(commit=False)
        image = form.cleaned_data['image']
        x1 = form.cleaned_data['x1']
        x2 = form.cleaned_data['x2']
        y2 = form.cleaned_data['y2']
        y1 = form.cleaned_data['y1']
        user.save()
        self.object = user
        club = ProfilePicture.objects.create(
            user=user, image=image, x1=x1, y1=y1, x2=x2, y2=y2)
        role = form.cleaned_data['role']

        if user.role == "Player":
            height = form.cleaned_data['height']
            weight = form.cleaned_data['weight']
            prefered_foot = form.cleaned_data['prefered_foot']
            favorite_position = form.cleaned_data['favorite_position']
            address_proof = form.cleaned_data['address_proof']
            age_proof = form.cleaned_data['age_proof']
            PlayerInfo.objects.create(official=user, height=height, weight=weight,
                                      prefered_foot=prefered_foot,
                                      favorite_position=favorite_position)
            AddressProof.objects.create(user=user, image=address_proof)
            AgeProof.objects.create(user=user, image=age_proof)

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if 'role' not in ctx:
            ctx['role'] = self.kwargs['role']
        return ctx

    def get_initial(self):
        initial = super().get_initial()
        if 'role' not in initial:
            initial = initial.copy()
            initial['role'] = self.kwargs['role']
        return initial

    def get_success_url(self):
        return reverse('OfficialsProfileView', kwargs={'pk': self.object.pk})


@method_decorator(verified_email_required, name='dispatch')
class UpdateClubDetails(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = ClubDetails
    fields = ['address', 'contact_number', 'date_of_formation']
    login_url = reverse_lazy('login')
    template_name = 'registration/officials_form.html'
    success_message = 'Club details has been updated'

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.club.user != self.request.user:
            return HttpResponseForbidden()
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('home')


@method_decorator(verified_email_required, name='dispatch')
class UpdateAddressProof(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = AddressProof
    form_class = AddressProofForm
    login_url = reverse_lazy('login')
    template_name = 'registration/officials_form.html'
    success_message = 'Address proof picture has been updated'

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.user.club.user != self.request.user:
            return HttpResponseForbidden()
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('OfficialsProfileView', kwargs={'pk': self.object.user.pk})


@method_decorator(verified_email_required, name='dispatch')
class UpdateAgeProof(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = AgeProof
    form_class = AgeProofForm
    login_url = reverse_lazy('login')
    template_name = 'registration/officials_form.html'
    success_message = 'Age proof picture has been updated'

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.user.club.user != self.request.user:
            return HttpResponseForbidden()
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('OfficialsProfileView', kwargs={'pk': self.object.user.pk})


@method_decorator(verified_email_required, name='dispatch')
class UpdateOfficialsImage(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = ProfilePicture
    form_class = ProfilePictureForm
    login_url = reverse_lazy('login')
    template_name = 'registration/officials_form.html'
    success_message = 'Profile picture has been updated'

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.user.club.user != self.request.user:
            return HttpResponseForbidden()
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('OfficialsProfileView', kwargs={'pk': self.object.user.pk})


@method_decorator(verified_email_required, name='dispatch')
class DeleteOfficials(LoginRequiredMixin, SuccessMessageMixin, DeleteView):
    login_url = reverse_lazy('login')
    model = Officials
    template_name = 'registration/officials_confirm_delete.html'
    success_message = 'Profile has been delete'

    def get_success_url(self):
        return reverse('home')

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.club.user != self.request.user:
            return HttpResponseForbidden()
        return super().dispatch(request, *args, **kwargs)


@method_decorator(verified_email_required, name='dispatch')
class DeleteInvitation(LoginRequiredMixin, SuccessMessageMixin, DeleteView):
    login_url = reverse_lazy('login')
    model = Invitations
    template_name = 'registration/officials_confirm_delete.html'
    success_message = 'Invitations has been deleted'

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.club.user != self.request.user:
            return HttpResponseForbidden()
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('home')


@method_decorator(verified_email_required, name='dispatch')
class AcceptInvitation(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    login_url = reverse_lazy('login')
    model = Officials
    fields = []
    template_name = 'registration/accept_invitation_confirm.html'
    success_message = 'Invitations has been accepted'

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.invitation.player != self.request.user:
            return HttpResponseForbidden()
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('home')

    def form_valid(self, form):
        form.instance.user = self.request.user
        official = form.save()
        Invitations.objects.filter(player=self.request.user).delete()
        return super().form_valid(form)


@method_decorator(verified_email_required, name='dispatch')
class LinkPlayer(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    login_url = reverse_lazy('login')
    form_class = LinkPlayerForm
    template_name = 'registration/officials_form.html'
    success_message = 'Official has been linked to a user'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['club'] = self.request.user.club
        return kwargs

    def get_success_url(self):
        return reverse('home')

    def form_valid(self, form):
        form.instance.club = self.request.user.club
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if 'profile' not in ctx:
            obj = get_object_or_404(Officials, pk=self.kwargs['pk'])
            ctx['profile'] = obj
        return ctx

    def get_initial(self):
        initial = super().get_initial()
        if 'profile' not in initial:
            initial = initial.copy()
            obj = get_object_or_404(Officials, pk=self.kwargs['pk'])
            initial['profile'] = obj
        return initial


@method_decorator(verified_email_required, name='dispatch')
class OfficialsProfileView(LoginRequiredMixin, DetailView):
    template_name = 'registration/officials_profile.html'
    login_url = reverse_lazy('login')
    model = Officials

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['edit'] = self.object.club.user == self.request.user
        return ctx


@method_decorator(verified_email_required, name='dispatch')
class ClubDetailView(LoginRequiredMixin, DetailView):
    template_name = 'registration/club_details.html'
    login_url = reverse_lazy('login')
    model = Club

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['jerseypictures'] = self.object.jerseypictures.all()
        ctx['clubdetails'] = self.object.clubdetails
        ctx['players'] = self.object.Officials.filter(
            role="Player")
        ctx['officials'] = self.object.Officials.exclude(
            role="Player")
        return ctx


class VerifyEmail(LoginRequiredMixin, UpdateView):
    model = get_user_model()
    fields = ['email']
    template_name = 'registration/email_verify.html'
    success_url = reverse_lazy('login')

    def dispatch(self, request, *args, **kwargs):
        reset = kwargs.get('reset', None)
        if self.request.user.email_verified:
            return redirect('home')
        elif reset:
            self.request.user.verification_email_send = False
            self.request.user.save()

        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        user = form.save()
        user.verification_email_send = True
        sendConfirm(user)
        return super().form_valid(form)
