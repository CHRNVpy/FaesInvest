# Generated by Django 5.0.6 on 2024-07-16 05:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mortgage_app', '0008_alter_propertycosthistory_created_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='property',
            name='closed',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='property',
            name='created',
            field=models.DateField(blank=True, null=True),
        ),
    ]
