# Generated by Django 3.1.1 on 2021-01-31 09:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('public', '0003_auto_20210131_0310'),
    ]

    operations = [
        migrations.CreateModel(
            name='Carousel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=20, unique=True)),
                ('title', models.CharField(blank=True, max_length=100)),
            ],
        ),
        migrations.AddField(
            model_name='carouselitem',
            name='cycles',
            field=models.PositiveIntegerField(default=1),
        ),
    ]
