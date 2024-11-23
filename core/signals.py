from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import Issue, Solution, DiagnosticStep, Question, Option, Map, MapCategory, IssueCategory
from .middleware import get_current_user

@receiver(pre_save, sender=Issue)
@receiver(pre_save, sender=Solution)
@receiver(pre_save, sender=DiagnosticStep)
@receiver(pre_save, sender=Question)
@receiver(pre_save, sender=Option)
@receiver(pre_save, sender=Map)
@receiver(pre_save, sender=MapCategory)
@receiver(pre_save, sender=IssueCategory)
def set_created_updated_by(sender, instance, **kwargs):
    user = get_current_user()  # دریافت کاربر فعلی از middleware
    if not instance.pk:  # اگر رکورد جدید باشد
        instance.created_by = user
    instance.updated_by = user