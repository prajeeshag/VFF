from django.shortcuts import render

from django.contrib.auth.views import LoginView as LoginViewCore

from django.contrib.auth.forms import UserCreationForm

from django.views.generic.edit import CreateView, UpdateView, DeleteView


class LoginView(LoginViewCore):
    template_name = 'account/login.html'


class SignupView(CreateView):
    form_class = UserCreationForm
    template_name = 'account/signup.html'
