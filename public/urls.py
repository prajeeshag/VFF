from django.urls import path
from django.contrib.auth.views import PasswordChangeView

from .views import (
    LandingPageView,
)

urlpatterns = [
    path('', LandingPageView.as_view(), name='landing_page'),
]
