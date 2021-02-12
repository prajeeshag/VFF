
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from django.contrib.auth.models import Permission

GROUPS = ['directors', 'league_executives', 'match_managers',
          'club_admins', 'players']


class Command(BaseCommand):
    help = 'Create groups'

    def handle(self, *args, **kwargs):
        for group in GROUPS:
            new_group, created = Group.objects.get_or_create(name=group)
            if created:
                print('New group created: {}'.format(group))
