# Generated by Django 3.1.1 on 2021-02-27 05:27

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0005_auto_20210129_0456'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='playerprofile',
            options={'ordering': ['first_name', 'last_name'], 'permissions': (('edit', 'Edit'),)},
        ),
    ]
