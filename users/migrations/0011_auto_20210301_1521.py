# Generated by Django 3.1.1 on 2021-03-01 09:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0010_auto_20210301_1504'),
    ]

    operations = [
        migrations.AddField(
            model_name='clubofficialsprofile',
            name='name',
            field=models.CharField(blank=True, max_length=100, verbose_name='Name'),
        ),
        migrations.AddField(
            model_name='clubofficialsprofile',
            name='nickname',
            field=models.CharField(blank=True, max_length=20, verbose_name='nickname'),
        ),
        migrations.AddField(
            model_name='playerprofile',
            name='name',
            field=models.CharField(blank=True, max_length=100, verbose_name='Name'),
        ),
        migrations.AddField(
            model_name='playerprofile',
            name='nickname',
            field=models.CharField(blank=True, max_length=20, verbose_name='nickname'),
        ),
    ]
