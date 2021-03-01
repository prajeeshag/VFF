# Generated by Django 3.1.1 on 2021-02-27 07:09

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('fixture', '0004_auto_20210212_1315'),
        ('match', '0009_auto_20210219_1617'),
    ]

    operations = [
        migrations.AlterField(
            model_name='suspension',
            name='completed_in',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='suspensions_completed', to='fixture.matches'),
        ),
        migrations.AlterField(
            model_name='suspension',
            name='got_in',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='suspensions', to='fixture.matches'),
        ),
    ]