# Generated by Django 3.1.1 on 2021-02-05 11:22

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('users', '0005_auto_20210129_0456'),
    ]

    operations = [
        migrations.CreateModel(
            name='Verification',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('verified', models.BooleanField(default=False)),
                ('request_review', models.BooleanField(default=False)),
                ('review_submitted', models.BooleanField(default=False)),
                ('review_comment', models.TextField(blank=True, max_length=300)),
                ('profile', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='users.playerprofile')),
            ],
        ),
    ]
