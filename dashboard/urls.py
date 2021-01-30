from django.urls import path, include
from rest_framework import routers

from . import views
from .public.views import urlpatterns as public_urlpatterns

app_name = 'dash'
urlpatterns = views.urlpatterns
urlpatterns += [path('public/', include(public_urlpatterns)), ]
