# management/commands/check_subscriptions.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import UserSubscription

class Command(BaseCommand):
    help = 'Deactivate or delete expired subscriptions'

    def handle(self, *args, **options):
        # اشتراک‌های منقضی شده
        expired_subs = UserSubscription.objects.filter(end_date__lt=timezone.now())

        # غیرفعال کردن (اگر از فیلد is_active استفاده میکنید)
        expired_subs.update(is_active=False)

        # یا حذف کامل
        # expired_subs.delete()

        self.stdout.write(self.style.SUCCESS(f'Successfully processed {expired_subs.count()} subscriptions.'))