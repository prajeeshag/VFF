from django.urls import path, include
from rest_framework import routers

from . import views

app_name = 'fixture'

router = routers.DefaultRouter()
router.register(r'fixtureinput', views.FixtureInputApi)

urlpatterns = []
urlpatterns += [path('', include(router.urls))]
