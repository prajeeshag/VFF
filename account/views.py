
from django.shortcuts import render, reverse
from django.utils.translation import ugettext_lazy as _

from django.contrib.auth.views import LoginView as LoginViewCore
from django.contrib.auth.forms import UserCreationForm

from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.contrib import messages

from formtools.wizard.views import SessionWizardView

from . import forms
from users.models import PhoneNumber, PlayerProfile, User


class LoginView(LoginViewCore):
    template_name = 'account/login.html'


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

        return reverse('login')
