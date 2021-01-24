from django.contrib import admin

from . import models


admin.site.register(models.Fixture)
admin.site.register(models.Matches)
