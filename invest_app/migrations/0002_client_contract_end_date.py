# Generated by Django 5.0.6 on 2024-06-21 05:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('invest_app', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='client',
            name='contract_end_date',
            field=models.DateField(blank=True, null=True),
        ),
    ]
