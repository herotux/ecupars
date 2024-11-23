import random
import django.core.validators
from django.db import migrations, models


def set_national_id(apps, schema_editor):
    CustomUser = apps.get_model('core', 'CustomUser')
    for user in CustomUser.objects.all():
        user.national_id = str(random.randint(10**9, 10**10 - 1))  # مقدار تصادفی 10 رقمی
        user.save()


def set_phone_number(apps, schema_editor):
    CustomUser = apps.get_model('core', 'CustomUser')
    for user in CustomUser.objects.all():
        user.phone_number = f'+{random.randint(10**9, 10**10 - 1)}'  # شماره تصادفی
        user.save()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_map_tags_mapcategory_alter_map_category'),
    ]

    operations = [
        # اضافه کردن فیلد city
        migrations.AddField(
            model_name='customuser',
            name='city',
            field=models.CharField(default='Default City', max_length=50),
            preserve_default=False,
        ),
        # اضافه کردن فیلد job
        migrations.AddField(
            model_name='customuser',
            name='job',
            field=models.CharField(default='Default Job', max_length=50),
            preserve_default=False,
        ),
        # اضافه کردن فیلد national_id (nullable به صورت موقت)
        migrations.AddField(
            model_name='customuser',
            name='national_id',
            field=models.CharField(
                max_length=10,
                unique=True,
                null=True,  # nullable به صورت موقت
            ),
        ),
        # مقداردهی national_id
        migrations.RunPython(set_national_id),
        # حذف nullable از فیلد national_id
        migrations.AlterField(
            model_name='customuser',
            name='national_id',
            field=models.CharField(
                max_length=10,
                unique=True,
            ),
        ),
        # اضافه کردن فیلد phone_number (nullable به صورت موقت)
        migrations.AddField(
            model_name='customuser',
            name='phone_number',
            field=models.CharField(
                max_length=15,
                unique=True,
                null=True,  # nullable به صورت موقت
            ),
        ),
        # مقداردهی phone_number
        migrations.RunPython(set_phone_number),
        # حذف nullable از فیلد phone_number
        migrations.AlterField(
            model_name='customuser',
            name='phone_number',
            field=models.CharField(
                max_length=15,
                unique=True,
                validators=[
                    django.core.validators.RegexValidator(regex='^\\+?1?\\d{9,15}$')
                ],
            ),
        ),
    ]