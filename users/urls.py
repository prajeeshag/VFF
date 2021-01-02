from django.urls import path

from .views import (
    LoginView,
)

urlpatterns = [
    path('', LoginView.as_view(redirect_authenticated_user=True)),
    path('login/', LoginView.as_view(redirect_authenticated_user=True), name='login'),
]
