from django.urls import path, include
from rest_framework import routers

from . import views
from .public.views import urlpatterns as public_urlpatterns
from .users.views import urlpatterns as users_urlpatterns
from .fixture.views import urlpatterns as fixture_urlpatterns
from .league.views import urlpatterns as league_urlpatterns
from .match.views import urlpatterns as match_urlpatterns

app_name = 'dash'
urlpatterns = views.urlpatterns
urlpatterns += [path('public/', include(public_urlpatterns)), ]
urlpatterns += [path('users/', include(users_urlpatterns)), ]
urlpatterns += [path('fixture/', include(fixture_urlpatterns)), ]
urlpatterns += [path('league/', include(league_urlpatterns)), ]
urlpatterns += [path('match/', include(match_urlpatterns)), ]
