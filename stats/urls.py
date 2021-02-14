from django.urls import path, include
from rest_framework import routers

from . import views

app_name = 'stats'
urlpatterns = views.urlpatterns
