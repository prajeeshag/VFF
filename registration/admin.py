from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Club, ClubDetails, Officials, PlayerInfo

admin.site.register(Club)
admin.site.register(ClubDetails)
admin.site.register(Officials)
admin.site.register(PlayerInfo)
