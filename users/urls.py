from django.urls import path, include
from rest_framework import routers

from . import views

app_name = 'users'

urlpatterns = [
    path('changepassword/', views.PasswordChange.as_view(), name='change_password'),
    path('home/', views.Home.as_view(), name='home'),
    path('unsignedplayers/', views.FreePlayersList.as_view(), name='unsignedplayers'),
    path('sendoffer/<int:pk>', views.CreateClubSigninOffer, name='signinoffer'),
    path('regectoffer/<int:pk>', views.RegectClubSigninOffer,
         name='regectsigninoffer'),
    path('acceptoffer/<int:pk>', views.AcceptClubSigninOffer,
         name='acceptsigninoffer'),
    path('canceloffer/<int:pk>', views.CancelClubSigninOffer,
         name='cancelsigninoffer'),
    path('clublist/', views.ClubList.as_view(), name='clublist'),
    path('clubmemberslist/<int:pk>/',
         views.ClubMembersList.as_view(), name='clubmemberslist'),
    path('clubdetails/<int:pk>/', views.ClubDetails.as_view(), name='clubdetails'),
    path('clubofficials/<int:pk>/', views.ClubOfficialsProfile.as_view(),
         name='clubofficialsprofile'),
    path('players/<int:pk>/', views.PlayersProfile.as_view(), name='playersprofile'),

    path('updateclub/', views.UpdateClubProfile.as_view(),
         name='updateclubprofile'),
    path('playerpdate/', views.UpdatePlayerProfile.as_view(),
         name='updateplayersprofile'),
    path('cluboffileupdate/<int:pk>/', views.ClubOfficialsProfileUpdate.as_view(),
         name='updateclubofficialsprofile'),
    path('dpedit/', views.dpEditView.as_view(), name='dpedit'),
    path('dpupload/', views.dpUploadView.as_view(), name='dpupload'),
]

# urlpatterns = [
#     path('addofficials/<str:role>/', AddOfficials.as_view(), name='AddOfficials'),


#     path('addjersey/',
#          AddJersey.as_view(), name='AddJersey'),

#     path('updatejersey/<int:pk>/',
#          UpdateJersey.as_view(), name='UpdateJersey'),

#     path('deletejersey/<int:pk>/',
#          DeleteJersey.as_view(), name='DeleteJersey'),

#     path('clubs/',
#          ClubListView.as_view(), name='ClubList'),

#     path('club/<int:pk>/',
#          ClubDetailView.as_view(), name='ClubDetail'),

#     path('officialslist/',
#          OfficialsListView.as_view(), name='officials_list_view'),

#     path('officialslist/<int:club>/',
#          OfficialsListView.as_view(), name='officials_list_view'),

#     path('dpedit1/<int:pk>/',
#          dpEditView.as_view(), name='dp_edit'),

#     path('dpupload/<int:pk>/',
#          dpUploadView.as_view(), name='dp_upload'),

#     path('dpedit/',
#          dpEditListView.as_view(), name='dp_edit_list'),

#     path('dpedit/<int:clubid>/',
#          dpEditListView.as_view(), name='dp_edit_list'),


#     path('abbr/<int:pk>/',
#          abbrUpdateView.as_view(), name='abbr'),

#     path('grnds/',
#          groundUpdateView.as_view(), name='grounds'),

#     path('clubgrnds/',
#          clubGrdUpdateView.as_view(), name='club_grounds'),
# ]
