from django.urls import path, include
from rest_framework import routers

from . import views

app_name = 'dash'

urlpatterns = [
    path('home/', views.Home.as_view(), name='home'),
    path('delplayer/<int:pk>/', views.del_player, name='delplayer'),
    path('calendar/', views.Calendar.as_view(), name='calendar'),
    path('editplayer/<int:pk>', views.EditPlayer.as_view(), name='editplayer'),
    path('playernumber/<int:pk>', views.EditPhoneNumber, name='editphone'),
    path('editemail/', views.UpdateEmail, name='editemail'),
]
