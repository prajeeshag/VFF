from django.shortcuts import render

from django.views.generic.edit import FormView

from . import forms


class PhoneVerification(FormView):
    template_name = 'account/phone_verification.html'
    form_class = forms.PhoneVerificationForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs
