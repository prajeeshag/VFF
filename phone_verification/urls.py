from django.urls import path

from . import views

urlpatterns = [
    path('phoneverify/', views.PhoneVerification.as_view(), name='verifyphone'),
]
