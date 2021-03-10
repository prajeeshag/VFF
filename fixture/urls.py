from django.urls import path, include
from rest_framework import routers

from . import views

app_name = 'fixture'

router = routers.DefaultRouter()
router.register(r'fixtureinput', views.FixtureInputApi)
router.register(r'matchinput', views.MatchInputApi)

# API
urlpatterns = [
    path('api/', include(router.urls)),
]
