
import os

from django.shortcuts import render, redirect
from django.urls import reverse_lazy, reverse
from django.utils.translation import ugettext_lazy as _

from django.contrib.auth.views import LoginView as LoginViewCore
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django.contrib import messages

from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.core.files.storage import FileSystemStorage
from django.contrib.auth.mixins import LoginRequiredMixin

from django.conf import settings

from formtools.wizard.views import SessionWizardView

from . import forms
from users.models import (PhoneNumber, PlayerProfile, User,
                          ProfilePicture, Document, Documents)


class LoginView(LoginViewCore):
    template_name = 'account/login.html'
    redirect_authenticated_user = True
    authentication_form = forms.LoginForm


class CreatePlayerProfile(SessionWizardView):
    template_name = 'account/create_profile.html'
    file_storage = FileSystemStorage(
        location=os.path.join(settings.MEDIA_ROOT, 'tmp'))

    form_list = [
        forms.PlayerProfileForm,
        forms.ProfilePictureForm,
        forms.DocumentForm1,
        forms.DocumentForm2,
    ]

    def done(self, form_list, **kwargs):
        forms = [form for form in form_list]  # get all forms
        user = self.request.user
        profile = forms[0].save(commit=False)
        profile.user = user

        dp = forms[1].save()
        profile.profilepicture = dp

        collection = Documents.objects.create()
        profile.documents = collection

        idproof = forms[2].save(commit=False)
        idproof.document_type = Document.PHOTOID
        idproof.collection = collection
        idproof.save()

        ageproof = forms[3].save(commit=False)
        ageproof.document_type = Document.AGEPROOF
        ageproof.collection = collection
        ageproof.save()

        profile.save()
        return redirect('users:home')


class PasswordResetView(SessionWizardView):
    template_name = 'account/password_reset.html'
    form_list = [
        forms.PassWordResetStep1,
        forms.PassWordResetStep2,
        forms.PassWordResetStep3,
    ]

    def get_form_kwargs(self, step=None):
        kwargs = super().get_form_kwargs(step)
        if step == '1':
            kwargs['request'] = self.request
            data = self.get_cleaned_data_for_step('0')
            kwargs['phone_number'] = data.get('phone_number')
        return kwargs

    # def get(self, request, *args, **kwargs):
        # try:
        # return self.render(self.get_form())
        # except KeyError:
        # return super().get(request, *args, **kwargs)

    def done(self, form_list, **kwargs):
        UserModel = get_user_model()
        forms = [form for form in form_list]  # get all forms
        password = forms[2].cleaned_data.get('password1')
        phone_number = forms[0].cleaned_data.get('phone_number')
        user = UserModel.objects.filter(
            phone_number__number=phone_number).distinct().first()
        user.set_password(password)
        user.save()

        messages.add_message(
            self.request, messages.SUCCESS,
            _('Password reset successful, login to continue..'))
        return redirect('login')


class SignupView(SessionWizardView):
    template_name = 'account/signup.html'
    form_list = [
        forms.SignupStep1,
        forms.SignupStep2,
    ]

    def get_form_kwargs(self, step=None):
        kwargs = super().get_form_kwargs(step)
        if step == '0':
            kwargs['request'] = self.request
        return kwargs

    def done(self, form_list, **kwargs):
        forms = [form for form in form_list]  # get all forms
        # get phone_number from first form
        # phone_number = forms[0].cleaned_data.get('phone_number')
        phone_number = forms[0].save()

        user = forms[1].save(commit=False)
        user_type = forms[1].cleaned_data.get('user_type')
        user.user_type = user_type
        user.email = None

        profile = None
        # check if phone_number is associated with a  profile already, link the user to the profile
        if user_type == User.PLAYER:
            profile = getattr(phone_number, 'playerprofile', None)
        if user_type == User.CLUBOFFICIAL:
            profile = getattr(phone_number, 'clubofficialsprofile', None)

        if profile:
            user.save()
            profile.user = user
            profile.phone_number = None
            profile.save()
            user.phone_number = phone_number
            user.save()
        else:
            phone_number.delete()
            phone_number = PhoneNumber.objects.create(
                number=phone_number, verified=True)
            user.phone_number = phone_number
            user.save()

        messages.add_message(
            self.request, messages.INFO,
            _('Account created, login to continue..'))

        return redirect('login')
