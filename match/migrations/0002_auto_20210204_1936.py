# Generated by Django 3.1.1 on 2021-02-04 14:06

import datetime
from django.db import migrations, models
import django.db.models.deletion
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('fixture', '0002_matches_status'),
        ('users', '0005_auto_20210129_0456'),
        ('match', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='events',
            name='time',
            field=models.DateTimeField(default=datetime.datetime(2021, 2, 4, 14, 6, 35, 968162, tzinfo=utc)),
        ),
        migrations.AlterField(
            model_name='squad',
            name='match',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='squad', to='fixture.matches'),
        ),
        migrations.CreateModel(
            name='AccumulatedCards',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('yellow', models.PositiveIntegerField(default=0)),
                ('player', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='users.playerprofile')),
            ],
        ),
        migrations.CreateModel(
            name='Suspension',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reason', models.CharField(choices=[('yellow', 'yellow'), ('Red', 'Red'), ('Other', 'Other')], max_length=20)),
                ('note', models.CharField(blank=True, max_length=100)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('active', models.BooleanField(default=True)),
                ('player', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.playerprofile')),
            ],
            options={
                'unique_together': {('player', 'created')},
            },
        ),
        migrations.CreateModel(
            name='Cards',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('color', models.CharField(choices=[('red', 'red'), ('yellow', 'yellow')], max_length=10)),
                ('time', models.DateTimeField(default=datetime.datetime(2021, 2, 4, 14, 6, 35, 967228, tzinfo=utc))),
                ('match', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='fixture.matches')),
                ('player', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.playerprofile')),
            ],
            options={
                'unique_together': {('player', 'match', 'color')},
            },
        ),
    ]
