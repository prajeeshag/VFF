from django.urls import path
from django.contrib.auth.views import LogoutView

from . import views

urlpatterns = [
    path('login/', views.LoginView.as_view(), name='account_login'),
    path('signup/', views.SignupView.as_view(), name='account_signup'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('passwdreset/', views.PasswordResetView.as_view(),
         name='account_reset_password'),
    path('login/', views.LoginView.as_view(), name='account_change_password'),
    path('logout/', LogoutView.as_view(), name='account_logout'),
    path('cplayerprofile/', views.CreatePlayerProfile.as_view(),
         name='create_player_profile')
]
