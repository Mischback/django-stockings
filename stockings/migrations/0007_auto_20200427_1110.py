# Generated by Django 3.0.5 on 2020-04-27 11:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stockings', '0006_auto_20200427_1105'),
    ]

    operations = [
        migrations.AlterField(
            model_name='portfolioitem',
            name='_deposit_timestamp',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='stockitem',
            name='_latest_price_timestamp',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]