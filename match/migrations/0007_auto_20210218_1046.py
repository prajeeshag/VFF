# Generated by Django 3.1.1 on 2021-02-18 05:16

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0005_auto_20210129_0456'),
        ('fixture', '0004_auto_20210212_1315'),
        ('match', '0006_auto_20210216_1702'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='squad',
            unique_together={('club', 'match', 'kind')},
        ),
    ]
