from django.urls import path
from django.contrib.auth.views import PasswordChangeView

from .views import (HomePageView, AddOfficials,
                    UpdateClubDetails, OfficialsProfileView,
                    AddJersey, UpdateJersey, LinkPlayer,
                    ClubListView, ClubDetailView, OfficialsListView,
                    DeleteJersey, DeleteInvitation, AcceptInvitation,
                    )

urlpatterns = [
    path('home/', HomePageView.as_view(), name='home'),
    path('addofficials/<str:role>/', AddOfficials.as_view(), name='AddOfficials'),

    path('linkplayer/<int:pk>/',
         LinkPlayer.as_view(), name='linkplayer'),

    path('DeleteInvitation/<int:pk>/',
         DeleteInvitation.as_view(), name='deleteinvitation'),

    path('AcceptInvitation/<int:pk>/',
         AcceptInvitation.as_view(), name='acceptinvitation'),

    path('officials/<int:pk>/',
         OfficialsProfileView.as_view(), name='OfficialsProfileView'),

    path('updateclubdetails/<int:pk>/',
         UpdateClubDetails.as_view(), name='UpdateClubDetails'),

    path('addjersey/',
         AddJersey.as_view(), name='AddJersey'),

    path('updatejersey/<int:pk>/',
         UpdateJersey.as_view(), name='UpdateJersey'),

    path('deletejersey/<int:pk>/',
         DeleteJersey.as_view(), name='DeleteJersey'),

    path('clubs/',
         ClubListView.as_view(), name='ClubList'),

    path('club/<int:pk>/',
         ClubDetailView.as_view(), name='ClubDetail'),

    path('officialslist/',
         OfficialsListView.as_view(), name='officials_list_view'),

    path('officialslist/<int:club>/',
         OfficialsListView.as_view(), name='officials_list_view'),
]
