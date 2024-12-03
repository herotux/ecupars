# Generated by Django 5.1.1 on 2024-11-27 22:07

import core.models
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0019_alter_subscription_expiry_date'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='customuser',
            name='access_level',
        ),
        migrations.AlterField(
            model_name='subscription',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='subscription_account', to=settings.AUTH_USER_MODEL),
        ),
        migrations.CreateModel(
            name='SubscriptionPlan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('access_to_all_categories', models.BooleanField(default=False)),
                ('access_to_diagnostic_steps', models.BooleanField(default=False)),
                ('price', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('restricted_categories', models.ManyToManyField(blank=True, to='core.issuecategory')),
            ],
        ),
        migrations.CreateModel(
            name='UserSubscription',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_date', models.DateTimeField()),
                ('end_date', models.DateTimeField(default=core.models.default_end_date)),
                ('active_categories', models.ManyToManyField(blank=True, to='core.issuecategory')),
                ('plan', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.subscriptionplan')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='subscription', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]