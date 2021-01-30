
import os

from django.shortcuts import render, redirect
from django.urls import reverse_lazy, reverse
from django.utils.translation import ugettext_lazy as _

from django.contrib.auth.views import (
    LoginView as LoginViewCore,
    PasswordResetView as PasswordResetCore,
    PasswordResetDoneView as PasswordResetDoneCore,
    PasswordResetConfirmView as PasswordResetConfirmCore,
)
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model, authenticate, login
from django.contrib import messages

from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.core.files.storage import FileSystemStorage
from django.contrib.auth.mixins import LoginRequiredMixin

from django.conf import settings

from formtools.wizard.views import SessionWizardView

from . import forms
from users.models import (PhoneNumber, PlayerProfile, User,
                          ProfilePicture, Document, Documents)

from core.mixins import viewMixins


class LoginView(viewMixins, LoginViewCore):
    template_name = 'account/login.html'
    redirect_authenticated_user = True
    authentication_form = forms.LoginForm
    extra_context = {'title': 'Login'}


class CreatePlayerProfile(viewMixins, SessionWizardView):
    template_name = 'account/create_profile.html'
    file_storage = FileSystemStorage(
        location=os.path.join(settings.MEDIA_ROOT, 'tmp'))
    extra_context = {'title': 'Create Player Profile'}

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
        return redirect('dash:home')


class PasswordResetConfirmView(viewMixins, PasswordResetConfirmCore):
    template_name = 'account/password_reset_confirm.html'


class PasswordResetEmail(viewMixins, PasswordResetCore):
    template_name = 'account/password_reset_email.html'


class PasswordResetDoneView(viewMixins, PasswordResetDoneCore):
    template_name = 'account/password_reset_done.html'


class PasswordResetView(viewMixins, SessionWizardView):
    template_name = 'account/password_reset.html'
    form_list = [
        forms.PassWordResetStep1,
        forms.PassWordResetStep3,
        forms.PassWordResetStep2,
    ]

    extra_context = {
        'title': 'Password Reset',
        'subtitles': [
            'Enter your phone number',
            'Enter the new password',
            'Enter OTP'
        ]
    }

    def get_form_kwargs(self, step=None):
        kwargs = super().get_form_kwargs(step)
        if step == '2':
            kwargs['request'] = self.request
            data = self.get_cleaned_data_for_step('0')
            kwargs['phone_number'] = data.get('phone_number')
        return kwargs

    def done(self, form_list, **kwargs):
        UserModel = get_user_model()
        forms = [form for form in form_list]  # get all forms
        password = forms[1].cleaned_data.get('password1')
        phone_number = forms[0].cleaned_data.get('phone_number')
        user = UserModel.objects.filter(
            phone_number__number=phone_number).distinct().first()
        user.set_password(password)
        user.save()

        messages.add_message(
            self.request, messages.SUCCESS,
            _('Password reset successful, login to continue..'))
        return redirect('login')


class SignupView(viewMixins, SessionWizardView):
    template_name = 'account/signup.html'
    form_list = [
        forms.SignupStep1,  # phone
        forms.SignupStep3,  # username
        forms.SignupStep2,  # otp
    ]
    extra_context = {
        'title': 'Create account',
        'subtitles': [
            'Enter your phone number',
            'Enter username and password',
            'Enter OTP recieved in your phone'
        ]
    }

    def get_form_kwargs(self, step=None):
        kwargs = super().get_form_kwargs(step)
        if step == '2':
            kwargs['request'] = self.request
            data = self.get_cleaned_data_for_step('0')
            kwargs['phone_number'] = data.get('phone_number')
        return kwargs

    def done(self, form_list, **kwargs):
        forms = [form for form in form_list]  # get all forms
        number = forms[0].cleaned_data.get('phone_number')
        phone_number, created = PhoneNumber.objects.get_or_create(
            number=number)
        phone_number.verified = True
        phone_number.save()

        user = forms[1].save(commit=False)
        user_type = forms[1].cleaned_data.get('user_type')
        password = forms[1].cleaned_data.get('password1')
        username = forms[1].cleaned_data.get('username')

        user.user_type = user_type

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

        user = authenticate(username=username, password=password)
        if (self.request.user.is_authenticated):
            logut(self.request)
        login(self.request, user)

        messages.add_message(
            self.request, messages.INFO,
            _('Account created....'))

        return redirect('login')
