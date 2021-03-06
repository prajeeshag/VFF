# Generated by Django 3.1.1 on 2021-01-27 02:31

import core.utils
import core.validators
from django.conf import settings
import django.contrib.auth.models
import django.contrib.auth.validators
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='username')),
                ('first_name', models.CharField(blank=True, max_length=150, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('user_type', models.CharField(choices=[('CLUB', 'Club Account'), ('PLAYER', 'Player'), ('CLUB OFFICIAL', 'Club Secretary/President/Manager'), ('OTHER', 'OTHER')], default='OTHER', max_length=50, verbose_name='User type')),
                ('email', models.EmailField(blank=True, max_length=254, null=True, unique=True, verbose_name='Email')),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.Group', verbose_name='groups')),
            ],
            options={
                'db_table': 'auth_user',
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='ClubProfile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True, verbose_name='Name')),
                ('address', models.TextField(max_length=200, verbose_name='Address')),
                ('pincode', models.CharField(max_length=10, validators=[core.validators.validate_Indian_pincode], verbose_name='Pincode')),
                ('year_of_formation', models.IntegerField(blank=True, null=True, verbose_name='Year of formation')),
                ('abbr', models.CharField(blank=True, max_length=4, null=True, unique=True, validators=[django.core.validators.MinLengthValidator(3)], verbose_name='Abbreviation')),
                ('registered', models.BooleanField(default=False, verbose_name='Registered')),
            ],
        ),
        migrations.CreateModel(
            name='Documents',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('num', models.PositiveIntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='Email',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(max_length=254, unique=True, verbose_name='Email')),
                ('verified', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Grounds',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True)),
                ('address', models.TextField(blank=True, max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='PhoneNumber',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.CharField(max_length=10, unique=True, validators=[core.validators.validate_phone_number], verbose_name='Phone number')),
                ('verified', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='ProfilePicture',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(max_length=255, upload_to=core.utils.get_image_upload_path)),
                ('x1', models.PositiveIntegerField(default=0, verbose_name='Cropbox (left)')),
                ('y1', models.PositiveIntegerField(default=0, verbose_name='Cropbox (top)')),
                ('x2', models.PositiveIntegerField(default=0, verbose_name='Cropbox (right)')),
                ('y2', models.PositiveIntegerField(default=0, verbose_name='Cropbox (bottom)')),
                ('checked', models.BooleanField(default=False)),
                ('orientation', models.PositiveSmallIntegerField(default=1)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='PlayerProfile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(max_length=100, verbose_name='First Name')),
                ('last_name', models.CharField(max_length=100, verbose_name='Last Name')),
                ('dob', models.DateField(verbose_name='Birthday')),
                ('address', models.TextField(max_length=200, verbose_name='Address')),
                ('pincode', models.CharField(max_length=10, validators=[core.validators.validate_Indian_pincode], verbose_name='Pincode')),
                ('student', models.BooleanField(default=False, verbose_name='Student')),
                ('occupation', models.CharField(blank=True, max_length=100, verbose_name='Occupation')),
                ('height', models.IntegerField(help_text='in Centimeters', verbose_name='Height (cm)')),
                ('weight', models.IntegerField(help_text='in Kilograms', verbose_name='Weight (kg)')),
                ('prefered_foot', models.CharField(choices=[('Left', 'Left foot'), ('Right', 'Right foot')], max_length=10)),
                ('favorite_position', models.CharField(choices=[('Defender', 'Defender'), ('Midfield', 'Midfield'), ('Forward', 'Forward'), ('Goalkeeper', 'Goalkeeper')], max_length=20)),
                ('club', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='players', to='users.clubprofile')),
                ('documents', models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, to='users.documents')),
                ('phone_number', models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, to='users.phonenumber')),
                ('profilepicture', models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, to='users.profilepicture')),
                ('user', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='PlayerCount',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('count', models.PositiveIntegerField(default=0)),
                ('club', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='playercount', to='users.clubprofile')),
            ],
        ),
        migrations.AddField(
            model_name='clubprofile',
            name='home_ground',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='club', to='users.grounds'),
        ),
        migrations.AddField(
            model_name='clubprofile',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='clubprofile', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='user',
            name='phone_number',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.PROTECT, to='users.phonenumber'),
        ),
        migrations.AddField(
            model_name='user',
            name='user_permissions',
            field=models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.Permission', verbose_name='user permissions'),
        ),
        migrations.CreateModel(
            name='Jersey',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(max_length=255, upload_to=core.utils.get_image_upload_path)),
                ('x1', models.PositiveIntegerField(default=0, verbose_name='Cropbox (left)')),
                ('y1', models.PositiveIntegerField(default=0, verbose_name='Cropbox (top)')),
                ('x2', models.PositiveIntegerField(default=0, verbose_name='Cropbox (right)')),
                ('y2', models.PositiveIntegerField(default=0, verbose_name='Cropbox (bottom)')),
                ('checked', models.BooleanField(default=False)),
                ('orientation', models.PositiveSmallIntegerField(default=1)),
                ('jersey_type', models.CharField(choices=[('Home', 'Home Jersey'), ('Away', 'Away Jersey'), ('Neutral', 'Neutral Jersey')], max_length=10, verbose_name='Jersey Type')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='jerseypictures', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('user', 'jersey_type')},
            },
        ),
        migrations.CreateModel(
            name='Document',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(max_length=255, upload_to=core.utils.get_image_upload_path)),
                ('x1', models.PositiveIntegerField(default=0, verbose_name='Cropbox (left)')),
                ('y1', models.PositiveIntegerField(default=0, verbose_name='Cropbox (top)')),
                ('x2', models.PositiveIntegerField(default=0, verbose_name='Cropbox (right)')),
                ('y2', models.PositiveIntegerField(default=0, verbose_name='Cropbox (bottom)')),
                ('checked', models.BooleanField(default=False)),
                ('orientation', models.PositiveSmallIntegerField(default=1)),
                ('document_type', models.CharField(choices=[('Photo ID', 'Photo ID proof'), ('Age Proof', 'Age proof')], max_length=50, verbose_name='Document Type')),
                ('collection', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='documents', to='users.documents')),
            ],
            options={
                'unique_together': {('collection', 'document_type')},
            },
        ),
        migrations.CreateModel(
            name='ClubSignings',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('accepted', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('club', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='clubsignings', to='users.clubprofile')),
                ('player', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='clubsignings', to='users.playerprofile')),
            ],
            options={
                'unique_together': {('club', 'player')},
            },
        ),
        migrations.CreateModel(
            name='ClubOfficialsProfile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(max_length=100, verbose_name='First Name')),
                ('last_name', models.CharField(max_length=100, verbose_name='Last Name')),
                ('dob', models.DateField(verbose_name='Birthday')),
                ('address', models.TextField(max_length=200, verbose_name='Address')),
                ('pincode', models.CharField(max_length=10, validators=[core.validators.validate_Indian_pincode], verbose_name='Pincode')),
                ('student', models.BooleanField(default=False, verbose_name='Student')),
                ('occupation', models.CharField(blank=True, max_length=100, verbose_name='Occupation')),
                ('role', models.CharField(choices=[('President', 'President of the Club'), ('Secretary', 'Secretary of the Club'), ('Manager', 'Manager of the Team')], max_length=10, verbose_name='Role')),
                ('club', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='officials', to='users.clubprofile')),
                ('phone_number', models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, to='users.phonenumber')),
                ('profilepicture', models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, to='users.profilepicture')),
                ('user', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('club', 'role')},
            },
        ),
    ]
