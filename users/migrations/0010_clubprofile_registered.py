# Generated by Django 3.1.1 on 2021-01-23 13:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0009_auto_20210121_2146'),
    ]

    operations = [
        migrations.AddField(
            model_name='clubprofile',
            name='registered',
            field=models.BooleanField(default=False, verbose_name='Registered'),
        ),
    ]
