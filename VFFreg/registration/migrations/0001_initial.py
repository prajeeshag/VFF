# Generated by Django 3.1.4 on 2020-12-17 17:23

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import registration.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Club',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('club_name', models.CharField(help_text='Name of the Club', max_length=50)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='club', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Officials',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(help_text='First name', max_length=100)),
                ('last_name', models.CharField(help_text='Last name/Initials', max_length=100)),
                ('date_of_birth', models.DateField()),
                ('address', models.TextField(help_text='Address', max_length=200)),
                ('phone_number', models.CharField(help_text='Mobile/Phone number', max_length=10)),
                ('email', models.EmailField(blank=True, help_text='Email Id', max_length=254)),
                ('occupation', models.CharField(blank=True, help_text='Occupation', max_length=100)),
                ('role', models.CharField(choices=[('President', 'President of the Club'), ('Secretary', 'Secretary of the Club'), ('Manager', 'Manager of the Football Team'), ('Player', 'Player')], max_length=10)),
                ('club', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='Officials', to='registration.club')),
                ('user', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='Official', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='ProfilePicture',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(max_length=255, upload_to=registration.models.get_image_upload_path)),
                ('x1', models.PositiveIntegerField(default=0, verbose_name='Cropbox (left)')),
                ('y1', models.PositiveIntegerField(default=0, verbose_name='Cropbox (top)')),
                ('x2', models.PositiveIntegerField(default=0, verbose_name='Cropbox (right)')),
                ('y2', models.PositiveIntegerField(default=0, verbose_name='Cropbox (bottom)')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profilepicture', to='registration.officials')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='PlayerInfo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('height', models.IntegerField(help_text='Height in Centimeters')),
                ('weight', models.IntegerField(help_text='Weight in Kilograms')),
                ('prefered_foot', models.CharField(choices=[('Left', 'Left foot'), ('Right', 'Right foot')], max_length=10)),
                ('favorite_position', models.CharField(choices=[('Defender', 'Defender'), ('Midfield', 'Midfield'), ('Forward', 'Forward'), ('Goalkeeper', 'Goalkeeper')], max_length=20)),
                ('official', models.OneToOneField(blank=True, on_delete=django.db.models.deletion.CASCADE, related_name='Player', to='registration.officials')),
            ],
        ),
        migrations.CreateModel(
            name='JerseyPicture',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(max_length=255, upload_to=registration.models.get_image_upload_path)),
                ('x1', models.PositiveIntegerField(default=0, verbose_name='Cropbox (left)')),
                ('y1', models.PositiveIntegerField(default=0, verbose_name='Cropbox (top)')),
                ('x2', models.PositiveIntegerField(default=0, verbose_name='Cropbox (right)')),
                ('y2', models.PositiveIntegerField(default=0, verbose_name='Cropbox (bottom)')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='jerseypictures', to='registration.club')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ClubDetails',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('address', models.TextField(help_text='Address of the Club', max_length=200)),
                ('contact_number', models.CharField(help_text='Contact number', max_length=10)),
                ('date_of_formation', models.IntegerField(blank=True, null=True, verbose_name='Year of formation of the Club')),
                ('club', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='clubdetails', to='registration.club')),
            ],
        ),
        migrations.CreateModel(
            name='AgeProof',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(max_length=255, upload_to=registration.models.get_image_upload_path)),
                ('x1', models.PositiveIntegerField(default=0, verbose_name='Cropbox (left)')),
                ('y1', models.PositiveIntegerField(default=0, verbose_name='Cropbox (top)')),
                ('x2', models.PositiveIntegerField(default=0, verbose_name='Cropbox (right)')),
                ('y2', models.PositiveIntegerField(default=0, verbose_name='Cropbox (bottom)')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='ageproof', to='registration.officials')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='AddressProof',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(max_length=255, upload_to=registration.models.get_image_upload_path)),
                ('x1', models.PositiveIntegerField(default=0, verbose_name='Cropbox (left)')),
                ('y1', models.PositiveIntegerField(default=0, verbose_name='Cropbox (top)')),
                ('x2', models.PositiveIntegerField(default=0, verbose_name='Cropbox (right)')),
                ('y2', models.PositiveIntegerField(default=0, verbose_name='Cropbox (bottom)')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='addressproof', to='registration.officials')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
