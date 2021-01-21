# Generated by Django 3.1.1 on 2021-01-21 19:14

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0007_auto_20210121_1702'),
    ]

    operations = [
        migrations.RenameField(
            model_name='phonenumber',
            old_name='phone_number',
            new_name='number',
        ),
        migrations.RemoveField(
            model_name='phonenumber',
            name='user',
        ),
        migrations.AddField(
            model_name='clubofficialsprofile',
            name='phone_number',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, to='users.phonenumber'),
        ),
        migrations.AddField(
            model_name='playerprofile',
            name='phone_number',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, to='users.phonenumber'),
        ),
        migrations.AlterField(
            model_name='phonenumber',
            name='verified',
            field=models.BooleanField(default=False),
        ),
    ]
