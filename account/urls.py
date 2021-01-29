from django.urls import path
from django.contrib.auth.views import LogoutView, PasswordResetConfirmView

from . import views

urlpatterns = [
    path('login/', views.LoginView.as_view(), name='account_login'),
    path('signup/', views.SignupView.as_view(), name='account_signup'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('passwdreset/', views.PasswordResetView.as_view(),
         name='account_reset_password'),
    path('logout/', LogoutView.as_view(), name='account_logout'),
    path('cplayerprofile/', views.CreatePlayerProfile.as_view(),
         name='create_player_profile'),
    path('passwdresetemail/', views.PasswordResetEmail.as_view(),
         name='account_reset_password_email'),
    path('passwdresetdone/', views.PasswordResetDoneView.as_view(),
         name='password_reset_done'),
    path('passwordresetconfirm/<str:uidb64>/<str:token>/',
         views.PasswordResetConfirmView.as_view(),
         name='password_reset_confirm'),
    path('login/', views.LoginView.as_view(), name='password_reset_complete'),
    path('logout/', LogoutView.as_view(), name='password_change_done'),
]
