from django.urls import path
from django.contrib.auth.views import PasswordChangeView

from . import views

urlpatterns = [
    path('', views.LandingPageView.as_view(), name='landing_page'),
    path('calendar/', views.Calendar.as_view(), name='calendar'),
]
