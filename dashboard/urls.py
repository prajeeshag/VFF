from django.urls import path, include
from rest_framework import routers

from . import views

app_name = 'dash'

urlpatterns = [
    path('home/', views.Home.as_view(), name='home'),
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
