# Generated by Django 5.0.6 on 2024-07-16 05:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mortgage_app', '0007_alter_property_options_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='propertycosthistory',
            name='created',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='propertyfundshare',
            name='date_of_change',
            field=models.DateField(),
        ),
    ]
