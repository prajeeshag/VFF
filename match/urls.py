from django.urls import path, include
from rest_framework import routers

from . import views

app_name = 'match'
urlpatterns = views.urlpatterns
