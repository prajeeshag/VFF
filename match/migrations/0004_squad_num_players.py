# Generated by Django 3.1.1 on 2021-02-08 09:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('match', '0003_auto_20210208_1427'),
    ]

    operations = [
        migrations.AddField(
            model_name='squad',
            name='num_players',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
