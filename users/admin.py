from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from . import models

admin.site.register(models.User, UserAdmin)
admin.site.register(models.ClubProfile)
admin.site.register(models.PhoneNumber)
admin.site.register(models.ProfilePicture)
