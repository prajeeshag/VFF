# Generated by Django 3.1.1 on 2021-03-01 09:28

import core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0008_remove_clubsignings_created_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='ph_number',
            field=models.CharField(blank=True, max_length=10, null=True, unique=True, validators=[core.validators.validate_phone_number], verbose_name='Phone number'),
        ),
        migrations.AlterField(
            model_name='user',
            name='email',
            field=models.EmailField(blank=True, max_length=254, null=True),
        ),
    ]
