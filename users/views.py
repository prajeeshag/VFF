from django.shortcuts import render

from django.contrib.auth.views import LoginView as LoginViewCore

from .forms import AuthenticationForm


class LoginView(LoginViewCore):
    form_class = AuthenticationForm
