# Generated by Django 5.1.1 on 2024-11-23 17:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0018_alter_subscription_expiry_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='subscription',
            name='expiry_date',
            field=models.DateTimeField(),
        ),
    ]
