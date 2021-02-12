from django.urls import path
from django.contrib.auth.views import PasswordChangeView

from . import views

app_name = 'public'

urlpatterns = [
    path('', views.LandingPageView.as_view(), name='home'),
]
