# Generated by Django 3.1.1 on 2021-01-24 12:53

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0010_clubprofile_registered'),
        ('fixture', '0003_auto_20210124_1236'),
    ]

    operations = [
        migrations.RenameField(
            model_name='matches',
            old_name='season',
            new_name='fixture',
        ),
        migrations.AlterUniqueTogether(
            name='matches',
            unique_together={('fixture', 'home', 'away', 'num')},
        ),
    ]
