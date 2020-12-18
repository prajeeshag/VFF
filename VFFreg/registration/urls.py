from django.urls import path
from .views import (SignUpView, HomePageView, AddOfficials,
                    UpdateOfficials, UpdateClubDetails, OfficialsProfileView,
                    UpdateOfficialsImage, AddJersey, UpdateJersey, DeleteOfficials,
                    DeleteJersey,
                    )

urlpatterns = [
    path('signup/', SignUpView.as_view(), name='signup'),
    path('home/', HomePageView.as_view(), name='home'),
    path('addofficials/<str:role>/', AddOfficials.as_view(), name='AddOfficials'),
    path('updateofficials/<int:pk>/',
         UpdateOfficials.as_view(), name='UpdateOfficials'),
    path('deleteofficials/<int:pk>/',
         DeleteOfficials.as_view(), name='DeleteOfficials'),
    path('updateimage/<int:pk>/',
         UpdateOfficialsImage.as_view(), name='UpdateOfficialsImage'),
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
]
