# Generated by Django 5.0.6 on 2024-07-09 09:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mortgage_app', '0002_alter_property_created'),
    ]

    operations = [
        migrations.AlterField(
            model_name='propertyfundshare',
            name='date_of_change',
            field=models.DateTimeField(),
        ),
    ]
