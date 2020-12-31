from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from django_email_verification import sendConfirm


def verified_email_required(
    function=None, login_url=None, redirect_field_name=REDIRECT_FIELD_NAME
):
    def decorator(view_func):
        @login_required(redirect_field_name=redirect_field_name, login_url=login_url)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_staff and request.user.email_verified:
                sendConfirm(request.user)
                request.user.verification_email_send = True
                return render(request, "registration/email_verify.html")
            return view_func(request, *args, **kwargs)
        return _wrapped_view

    if function:
        return decorator(function)
    return decorator
