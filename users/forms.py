from django.contrib.auth.forms import AuthenticationForm as AuthenticationFormCore
from django.contrib.auth.forms import UsernameField
from django import forms


class AuthenticationForm(AuthenticationFormCore):
    username = UsernameField(label='Username or Email',
                             widget=forms.TextInput(attrs={'autofocus': True}))
