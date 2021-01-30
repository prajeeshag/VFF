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

from extra_views import UpdateWithInlinesView, InlineFormSetFactory, ModelFormSetView


from .forms import (
    SignUpFormClub, OfficialsCreationForm, PlayerCreationForm,
    ProfilePictureForm, AddressProofForm, AgeProofForm,
    SignUpFormPersonal, LinkPlayerForm, dpEditForm, dpFormSet,
    dpUploadForm, OfficialsEditForm, abbrForm, clubDetailsForm
)
from .models import (
    Officials, PlayerInfo, Club, ClubDetails, JerseyPicture,
    ProfilePicture, AddressProof, AgeProof, Invitations, Grounds
)



class HomePageView(LoginRequiredMixin, TemplateView):
    template_name = 'registration/home.html'
    login_url = reverse_lazy('login')

    def dispatch(self, request, *args, **kwargs):
        return redirect('ClubList')


class OfficialsListView(LoginRequiredMixin, TemplateView):
    template_name = 'registration/officials_list.html'
    login_url = reverse_lazy('login')
    breadcrumbs = [
        ('Club List', 'ClubList'),
        ('List of People', None),
    ]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        clubpk = self.kwargs.get('club', None)
        if clubpk:
            obj = get_object_or_404(Club, pk=clubpk)
            ctx['officials'] = obj.Officials.all()
            ctx['title'] = "Member's of {}".format(obj)
            ctx['club'] = True
        else:
            ctx['officials'] = Officials.objects.all()
            ctx['title'] = "Member's of VFL"
            ctx['club'] = False
        return ctx


class ClubListView(LoginRequiredMixin, TemplateView):
    template_name = 'registration/club_list.html'
    login_url = reverse_lazy('login')
    breadcrumbs = [('Club List', None), ]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['clubs'] = Club.objects.filter(user__is_active=True)
        return ctx


class AddJersey(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = JerseyPicture
    fields = ['image']
    login_url = reverse_lazy('login')
    template_name = 'registration/jersey_form.html'
    success_message = 'Jersey has been added'

    def form_valid(self, form):
        form.instance.user = self.request.user.club
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('home')

    def get_breadcrumbs(self):
        bc = super().get_breadcrumbs()
        bc.append(self.make_breadcrumbs(
            viewname='ClubDetail', obj=self.request.user.club))
        bc.append(self.make_breadcrumbs(name='Add Jersey'))
        return bc


class DeleteJersey(LoginRequiredMixin, SuccessMessageMixin, DeleteView):
    model = JerseyPicture
    login_url = reverse_lazy('login')
    template_name = 'registration/jersey_confirm_delete.html'
    success_message = 'Jersey has been deleted'

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.user.user != self.request.user:
            return HttpResponseForbidden()
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('ClubDetail', kwargs={'pk': self.object.club.pk})

    def get_breadcrumbs(self):
        bc = super().get_breadcrumbs()
        bc.append(self.make_breadcrumbs(
            viewname='ClubDetail', obj=self.object.user))
        bc.append(self.make_breadcrumbs(name='Delete Jersey'))
        return bc


class UpdateJersey(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = JerseyPicture
    fields = ['image']
    login_url = reverse_lazy('login')
    template_name = 'registration/jersey_form.html'
    success_message = 'Jersey has been updated'

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.user.user != self.request.user:
            return HttpResponseForbidden()
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('ClubDetail', kwargs={'pk': self.object.club.pk})

    def get_breadcrumbs(self):
        bc = super().get_breadcrumbs()
        bc.append(self.make_breadcrumbs(
            viewname='ClubDetail', obj=self.object.user))
        bc.append(self.make_breadcrumbs(name='Update Jersey'))
        return bc


class AddOfficials(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    login_url = reverse_lazy('login')
    form_class = OfficialsCreationForm
    template_name = 'registration/add_officials_form.html'
    success_message = 'Profile has been created'

    def get_breadcrumbs(self):
        bc = super().get_breadcrumbs()
        bc.append(self.make_breadcrumbs(
            viewname='ClubDetail', obj=self.request.user.club))
        bc.append(self.make_breadcrumbs(name='Add '+self.kwargs['role']))
        return bc

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


class UpdateClubDetails(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = ClubDetails
    form_class = clubDetailsForm
    login_url = reverse_lazy('login')
    template_name = 'registration/club_detail_form.html'
    success_message = 'Club details has been updated'

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.club.user != self.request.user:
            return HttpResponseForbidden()
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('ClubDetail', kwargs={'pk', self.object.pk})

    def get_breadcrumbs(self):
        bc = super().get_breadcrumbs()
        bc.append(self.make_breadcrumbs(
            viewname='ClubDetail', obj=self.object.club))
        bc.append(self.make_breadcrumbs(name='details'))
        return bc


class UpdateAddressProof(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = AddressProof
    form_class = AddressProofForm
    login_url = reverse_lazy('login')
    template_name = 'registration/address_proof_form.html'
    success_message = 'Address proof picture has been updated'

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.user.club.user != self.request.user:
            return HttpResponseForbidden()
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('OfficialsProfileView', kwargs={'pk': self.object.user.pk})


class UpdateAgeProof(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = AgeProof
    form_class = AgeProofForm
    login_url = reverse_lazy('login')
    template_name = 'registration/age_proof_form.html'
    success_message = 'Age proof picture has been updated'

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.user.club.user != self.request.user:
            return HttpResponseForbidden()
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('OfficialsProfileView', kwargs={'pk': self.object.user.pk})


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


class DeleteInvitation(LoginRequiredMixin, SuccessMessageMixin, DeleteView):
    login_url = reverse_lazy('login')
    model = Invitations
    template_name = 'registration/invitation_confirm_delete.html'
    success_message = 'Invitations has been deleted'

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.club.user != self.request.user:
            return HttpResponseForbidden()
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('home')


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


class LinkPlayer(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    login_url = reverse_lazy('login')
    form_class = LinkPlayerForm
    template_name = 'registration/link_player_form.html'
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


class OfficialsProfileView(LoginRequiredMixin, DetailView):
    template_name = 'registration/officials_profile.html'
    login_url = reverse_lazy('login')
    model = Officials

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        return ctx

    def get_breadcrumbs(self):
        bc = super().get_breadcrumbs()
        bc.append(self.make_breadcrumbs(
            viewname='ClubDetail', obj=self.object.club))
        bc.append(self.make_breadcrumbs(name=self.object.role))
        return bc


class ClubDetailView(LoginRequiredMixin, DetailView):
    template_name = 'registration/club_detail.html'
    login_url = reverse_lazy('login')
    model = Club
    breadcrumbs = [('Club List', 'ClubList'), ]

    def get_breadcrumbs(self):
        bc = super().get_breadcrumbs()
        bc.append(self.make_breadcrumbs(
            viewname='ClubDetail', obj=self.object))
        return bc

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['jerseypictures'] = self.object.jerseypictures.all()
        ctx['clubdetails'] = self.object.clubdetails
        ctx['players'] = self.object.Officials.filter(
            role="Player")
        ctx['officials'] = self.object.Officials.exclude(
            role="Player")
        return ctx


class dpUploadView(LoginRequiredMixin, UpdateView):
    model = ProfilePicture
    form_class = dpUploadForm
    template_name = 'registration/dp_upload.html'

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if (not self.request.user.is_staff and
                obj.user.club.user != self.request.user):
            return HttpResponseForbidden()
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return self.object.get_absolute_url()


class dpEditView(LoginRequiredMixin, UpdateView):
    model = ProfilePicture
    form_class = dpEditForm
    template_name = 'registration/dp_edit.html'

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if (not self.request.user.is_staff and
                obj.user.club.user != self.request.user):
            return HttpResponseForbidden()
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('OfficialsProfileView', kwargs={'pk': self.object.user.pk})


class officialsEditView(LoginRequiredMixin, UpdateView):
    model = Officials
    form_class = OfficialsEditForm
    template_name = 'registration/officials_edit_form.html'

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if (not self.request.user.is_staff and
                obj.club.user != self.request.user):
            return HttpResponseForbidden()
        return super().dispatch(request, *args, **kwargs)


class dpEditListView(LoginRequiredMixin, ModelFormSetView):
    model = ProfilePicture
    form_class = dpEditForm
    formset_class = dpFormSet
    template_name = 'registration/dp_edit_list.html'
    factory_kwargs = {'extra': 0, 'max_num': 10}

    def get_success_url(self):
        clubid = self.kwargs.get('clubid', None)
        if clubid:
            return reverse('dp_edit_list', kwargs={'clubid': clubid})
        return reverse('dp_edit_list')

    def get_formset_kwargs(self):
        kwargs = super(ModelFormSetView, self).get_formset_kwargs()
        if 'clubid' in self.kwargs:
            kwargs['clubid'] = self.kwargs['clubid']
        return kwargs


class groundUpdateView(LoginRequiredMixin, ModelFormSetView):
    model = Grounds
    fields = ['name', ]
    template_name = 'registration/grounds_form.html'
    factory_kwargs = {'extra': 10, 'max_num': 50}

    def get_success_url(self):
        return reverse('grounds')


class clubGrdUpdateView(LoginRequiredMixin, ModelFormSetView):
    model = ClubDetails
    fields = ['home_ground', ]
    template_name = 'registration/club_ground_form.html'
    factory_kwargs = {'extra': 0, 'max_num': 0}

    def get_success_url(self):
        return reverse('club_grounds')
