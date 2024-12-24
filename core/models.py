from django.db import models
from django_ckeditor_5.fields import CKEditor5Field
from django.core.validators import RegexValidator
from django.db.models import Q
from django.conf import settings
from django.contrib.auth.models import AbstractUser, Group, Permission
import string
import uuid
from django.utils import timezone
from django_jalali.db import models as jmodels
from django.utils.timezone import now
from datetime import timedelta






def default_end_date():
    return now() + timedelta(days=30)


def default_start_date():
    return now()


class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'مدیر'),
        ('normal', 'کاربر'),
        ('premium', 'کاربر ویژه'),
    )
 
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='normal')
    national_id = models.CharField(max_length=10, unique=True)
    city = models.CharField(max_length=50)
    job = models.CharField(max_length=50)
    phone_number = models.CharField(
        max_length=15,
        unique=True,
        validators=[RegexValidator(regex=r'^\+?1?\d{9,15}$')]
    )
    hardware_id = models.CharField(max_length=255, null=True, blank=True)
    license_key = models.CharField(max_length=255, null=True, blank=True)
    groups = models.ManyToManyField(
        Group,
        related_name='customuser_set',
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups'
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='customuser_set',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions'
    )

    def __str__(self):
        return self.username


class LoginSession(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    session_id = models.UUIDField(default=uuid.uuid4, unique=True)
    otp = models.CharField(max_length=6, null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    created_at = jmodels.jDateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Session {self.session_id} for {self.user.username}"


class IssueCategory(models.Model):
    name = models.CharField(max_length=100)
    order = models.IntegerField(null=True, blank=True, unique=True) 
    parent_category = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='subcategories')
    created_at = jmodels.jDateTimeField(auto_now_add=True)
    updated_at = jmodels.jDateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="issue_category_creators")
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="issue_category_updaters")
    logo = models.FileField(upload_to='logos/issue_categories/', null=True, blank=True)

    def __str__(self):
        return self.name

    def get_full_category_name(self):
        names = []
        current_category = self
        while current_category:
            names.append(current_category.name)
            current_category = current_category.parent_category
        return ' > '.join(reversed(names))


class MapCategory(models.Model):
    name = models.CharField(max_length=100)
    order = models.IntegerField(null=True, blank=True, unique=True) 
    parent_category = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='subcategories')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="map_category_creators")
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="map_category_updaters")
    created_at = jmodels.jDateTimeField(auto_now_add=True)
    updated_at = jmodels.jDateTimeField(auto_now=True)
    
    logo = models.FileField(upload_to='logos/map_categories/', null=True, blank=True)

    def __str__(self):
        return self.name

    def get_full_category_name(self):
        names = []
        current_category = self
        while current_category:
            names.append(current_category.name)
            current_category = current_category.parent_category
        return ' > '.join(reversed(names))


class Issue(models.Model):
    title = models.CharField(max_length=200)
    description = CKEditor5Field('Text', config_name='extends')
    category = models.ForeignKey(IssueCategory, on_delete=models.CASCADE)
    question = models.ForeignKey('Question', on_delete=models.SET_NULL, blank=True, null=True)
    tags = models.ManyToManyField('Tag', related_name='issues', blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="issue_creators")
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="issue_updaters")
    created_at = jmodels.jDateTimeField(auto_now_add=True)
    updated_at = jmodels.jDateTimeField(auto_now=True)

    def __str__(self):
        return self.title
    
    def delete(self, *args, **kwargs):
        if self.question:
            self.question.delete()
        super(Issue, self).delete(*args, **kwargs)


class Solution(models.Model):
    issues = models.ManyToManyField(Issue, related_name='solutions', blank=True)
    title = models.CharField(max_length=200)
    description = CKEditor5Field('Text', config_name='extends')
    tags = models.ManyToManyField('Tag', related_name='solutions', blank=True)
    is_public = models.BooleanField(default=False)
    created_at = jmodels.jDateTimeField(auto_now_add=True)
    updated_at = jmodels.jDateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="solution_creators")
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="solution_updaters")

    def __str__(self):
        return self.title
    
    @classmethod
    def get_filtered_solutions(cls, issue_id=None):
        if issue_id is not None:
            return cls.objects.filter(Q(is_public=True) | Q(issues__id=issue_id)).distinct()
        else:
            return cls.objects.filter(is_public=True)

    def get_issue_hierarchy(self):
        hierarchy = {}
        for issue in self.issues.all():
            hierarchy[issue.title] = issue.category.get_full_category_name()
        return hierarchy

    def get_solution_title_by_issue_id(self, issue_id):
        solutions = self.objects.filter(issues__id=issue_id)
        titles = [solution.title for solution in solutions]
        return titles


class Map(models.Model):
    title = models.CharField(max_length=255)
    image = models.ImageField(upload_to='maps/')
    category = models.ForeignKey(MapCategory, on_delete=models.CASCADE)
    tags = models.ManyToManyField('Tag', related_name='maps', blank=True)
    created_at = jmodels.jDateTimeField(auto_now_add=True)
    updated_at = jmodels.jDateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="map_creators")
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="map_updaters")

    def __str__(self):
        return self.title


class DiagnosticStep(models.Model):
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, related_name='diagnostic_steps')
    solution = models.ForeignKey(Solution, on_delete=models.SET_NULL, blank=True, null=True)
    letter = models.CharField(max_length=1, editable=False)
    map = models.ForeignKey(Map, on_delete=models.SET_NULL, blank=True, null=True, related_name='diagnostic_steps')
    question = models.ForeignKey('Question', on_delete=models.SET_NULL, blank=True, null=True)
    has_cycle = models.BooleanField(default=False)
    created_at = jmodels.jDateTimeField(auto_now_add=True)
    updated_at = jmodels.jDateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="diagnostic_step_creators")
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="diagnostic_step_updaters")

    def save(self, *args, **kwargs):
        if not self.letter:
            steps = DiagnosticStep.objects.filter(issue=self.issue)
            if steps.exists():
                used_letters = set(step.letter for step in steps)
                for letter in string.ascii_uppercase:
                    if letter not in used_letters:
                        self.letter = letter
                        break
            else:
                self.letter = 'A'
        super().save(*args, **kwargs)


class Subscription(models.Model):
    ACCESS_LEVEL_CHOICES = (
        (1, 'کاربر سطح 1'),
        (2, 'کاربر سطح 2'),
        (3, 'کاربر سطح 3'),
        (4, 'کاربر سطح 4'),
    )
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='subscription_account')
    access_level = models.IntegerField(choices=ACCESS_LEVEL_CHOICES, default=1)
    active = models.BooleanField(default=False)
    expiry_date = models.DateTimeField()  

    def is_active(self):
        return self.active and (self.expiry_date is None or self.expiry_date >= timezone.now())


class Bookmark(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='bookmarks')
    url = models.URLField()
    title = models.CharField(max_length=200)
    created_at = jmodels.jDateTimeField(auto_now_add=True)
    updated_at = jmodels.jDateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} by {self.user.username}"


class Question(models.Model):
    text = models.CharField(max_length=255)
    created_at = jmodels.jDateTimeField(auto_now_add=True)
    updated_at = jmodels.jDateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="question_creators")
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="question_updaters")

    def __str__(self):
        return self.text


class Option(models.Model):
    text = models.CharField(max_length=255)
    question = models.ForeignKey(Question, related_name='options', on_delete=models.CASCADE)
    next_step = models.ForeignKey('DiagnosticStep', null=True, blank=True, on_delete=models.SET_NULL, related_name='prev_options')
    issue = models.ForeignKey(Issue, null=True, blank=True, on_delete=models.SET_NULL, related_name='back_to_issue')
    created_at = jmodels.jDateTimeField(auto_now_add=True)
    updated_at = jmodels.jDateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="option_creators")
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="option_updaters")

    def __str__(self):
        return self.text


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name



class UserActivity(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    login_time = models.DateTimeField(auto_now_add=True)
    logout_time = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Activity for {self.user.username} - Login: {self.login_time}, Logout: {self.logout_time}"





class SubscriptionPlan(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)
    access_to_all_categories = models.BooleanField(default=False)
    access_to_diagnostic_steps = models.BooleanField(default=False)
    restricted_categories = models.ManyToManyField('IssueCategory', blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    def __str__(self):
        return self.name




# اشتراک کاربران
class UserSubscription(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name="subscription")
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE)
    active_categories = models.ManyToManyField(IssueCategory, blank=True)  
    start_date = models.DateTimeField(default=default_start_date)
    end_date = models.DateTimeField(default=default_end_date)  

    def is_active(self):
        return self.end_date > now()

    def __str__(self):
        return f"{self.user.username} - {self.plan.name}"





class Advertisement(models.Model):
    
    title = models.CharField(max_length=255, verbose_name="عنوان")
    link = models.URLField(verbose_name="لینک")
    banner = models.ImageField(upload_to='advertisements/', verbose_name="بنر")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "تبلیغ"
        verbose_name_plural = "تبلیغات"

    def __str__(self):
        return self.title


class ChatSession(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='user_sessions', on_delete=models.CASCADE)
    consultant = models.ForeignKey(User, related_name='consultant_sessions', null=True, blank=True, on_delete=models.SET_NULL)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Chat between {self.user.username} and {self.consultant.username if self.consultant else 'Unassigned'}"

class Message(models.Model):
    session = models.ForeignKey(ChatSession, related_name='messages', on_delete=models.CASCADE)
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.sender.username} at {self.timestamp}"