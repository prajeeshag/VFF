# Generated by Django 3.1.4 on 2020-12-30 12:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0007_auto_20201230_1153'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='user_type',
            field=models.CharField(choices=[('CLUB', 'Club Account'), ('PERSONAL', 'Personal Account (For players/officials)')], default='PERSONAL', max_length=10),
        ),
    ]
