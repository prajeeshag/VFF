# Generated by Django 3.1.1 on 2021-01-28 15:18

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_auto_20210128_0409'),
    ]

    operations = [
        migrations.AddField(
            model_name='clubprofile',
            name='logo',
            field=models.FileField(null=True, upload_to='logo/club/', validators=[django.core.validators.FileExtensionValidator(['svg'])]),
        ),
    ]
