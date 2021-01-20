from django.contrib.auth.forms import AuthenticationForm as AuthenticationFormCore
from django.contrib.auth.forms import UsernameField
from django import forms

from allauth.account.forms import (
    SignupForm as SignupFormAllAuth,
    LoginForm as LoginFormAllAuth
)

from captcha.fields import ReCaptchaField

class AuthenticationForm(AuthenticationFormCore):
    username = UsernameField(label='Username or Email',
                             widget=forms.TextInput(attrs={'autofocus': True}))


class SignupForm(SignupFormAllAuth):
    captcha = ReCaptchaField()
    field_order = ['email', 'password1', 'password2', 'captcha']

class LoginForm(LoginFormAllAuth):
    captcha = ReCaptchaField()
    field_order = ['username', 'password', 'captcha']
