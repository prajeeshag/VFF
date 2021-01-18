# Generated by Django 3.1.1 on 2021-01-18 15:02

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registration', '0012_auto_20210111_1848'),
    ]

    operations = [
        migrations.AddField(
            model_name='clubdetails',
            name='abbr',
            field=models.CharField(blank=True, max_length=4, null=True, unique=True, validators=[django.core.validators.MinLengthValidator(3)], verbose_name='Club abbreviation(3-4 characters)'),
        ),
    ]
