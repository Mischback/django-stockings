# Generated by Django 3.0.5 on 2020-04-28 13:06

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('stockings', '0007_auto_20200427_1110'),
    ]

    operations = [
        migrations.AlterField(
            model_name='portfolioitem',
            name='_deposit_timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name='stockitem',
            name='_latest_price_timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
