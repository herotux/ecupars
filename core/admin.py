from django.contrib import admin
from django.utils import timezone

from django.utils.translation import gettext_lazy as _

admin.site.site_header = _("ECUPARS")
admin.site.site_title = _("ECUPARS")
admin.site.index_title = _("ECUPARS")



from .models import (
    CustomUser,
    LoginSession,
    IssueCategory,
    MapCategory,
    Issue,
    Solution,
    Map,
    DiagnosticStep,
    Subscription,
    Bookmark,
    Question,
    Option,
    Tag,
    UserActivity,
)

def format_datetime(value):
    if value is not None:
        return timezone.localtime(value).strftime('%Y-%m-%d %H:%M:%S')
    return ''

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'role', 'access_level', 'national_id', 'city', 'job', 'phone_number')
    search_fields = ('username', 'email', 'national_id', 'phone_number')
    list_filter = ('role',)

    def username(self, obj):
        return obj.username
    username.short_description = 'نام کاربری'


@admin.register(LoginSession)
class LoginSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'session_id', 'is_verified', 'created_at_formatted')
    search_fields = ('user__username', 'session_id')

    def created_at_formatted(self, obj):
        return format_datetime(obj.created_at)
    created_at_formatted.short_description = 'تاریخ ایجاد'


@admin.register(IssueCategory)
class IssueCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at_formatted', 'updated_at_formatted', 'created_by', 'updated_by')
    search_fields = ('name',)

    def created_at_formatted(self, obj):
        return format_datetime(obj.created_at)
    created_at_formatted.short_description = 'تاریخ ایجاد'

    def updated_at_formatted(self, obj):
        return format_datetime(obj.updated_at)
    updated_at_formatted.short_description = 'تاریخ به‌روزرسانی'


@admin.register(MapCategory)
class MapCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at_formatted', 'updated_at_formatted')
    search_fields = ('name',)

    def created_at_formatted(self, obj):
        return format_datetime(obj.created_at)
    created_at_formatted.short_description = 'تاریخ ایجاد'

    def updated_at_formatted(self, obj):
        return format_datetime(obj.updated_at)
    updated_at_formatted.short_description = 'تاریخ به‌روزرسانی'


@admin.register(Issue)
class IssueAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'created_at_formatted', 'updated_at_formatted', 'created_by', 'updated_by')
    search_fields = ('title',)

    def created_at_formatted(self, obj):
        return format_datetime(obj.created_at)
    created_at_formatted.short_description = 'تاریخ ایجاد'

    def updated_at_formatted(self, obj):
        return format_datetime(obj.updated_at)
    updated_at_formatted.short_description = 'تاریخ به‌روزرسانی'


@admin.register(Solution)
class SolutionAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_public', 'created_at_formatted', 'updated_at_formatted', 'created_by', 'updated_by')
    search_fields = ('title',)

    def created_at_formatted(self, obj):
        return format_datetime(obj.created_at)
    created_at_formatted.short_description = 'تاریخ ایجاد'

    def updated_at_formatted(self, obj):
        return format_datetime(obj.updated_at)
    updated_at_formatted.short_description = 'تاریخ به‌روزرسانی'


@admin.register(Map)
class MapAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'created_at_formatted', 'updated_at_formatted', 'created_by', 'updated_by')
    search_fields = ('title',)

    def created_at_formatted(self, obj):
        return format_datetime(obj.created_at)
    created_at_formatted.short_description = 'تاریخ ایجاد'

    def updated_at_formatted(self, obj):
        return format_datetime(obj.updated_at)
    updated_at_formatted.short_description = 'تاریخ به‌روزرسانی'


@admin.register(DiagnosticStep)
class DiagnosticStepAdmin(admin.ModelAdmin):
    list_display = ('issue', 'letter', 'created_at_formatted', 'updated_at_formatted', 'created_by', 'updated_by')
    search_fields = ('issue__title',)

    def created_at_formatted(self, obj):
        return format_datetime(obj.created_at)
    created_at_formatted.short_description = 'تاریخ ایجاد'

    def updated_at_formatted(self, obj):
        return format_datetime(obj.updated_at)
    updated_at_formatted.short_description = 'تاریخ به‌روزرسانی'


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'access_level', 'active', 'expiry_date', 'status_display')
    search_fields = ('user__username',)

    def status_display(self, obj):
        return "فعال" if obj.is_active() else "غیرفعال"
    status_display.short_description = 'وضعیت'


@admin.register(Bookmark)
class BookmarkAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'created_at_formatted')
    search_fields = ('user__username', 'title')

    def created_at_formatted(self, obj):
        return format_datetime(obj.created_at)
    created_at_formatted.short_description = 'تاریخ ایجاد'


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'created_at_formatted', 'updated_at_formatted', 'created_by', 'updated_by')
    search_fields = ('text',)

    def created_at_formatted(self, obj):
        return format_datetime(obj.created_at)
    created_at_formatted.short_description = 'تاریخ ایجاد'

    def updated_at_formatted(self, obj):
        return format_datetime(obj.updated_at)
    updated_at_formatted.short_description = 'تاریخ به‌روزرسانی'


@admin.register(Option)
class OptionAdmin(admin.ModelAdmin):
    list_display = ('text', 'question', 'created_at_formatted', 'updated_at_formatted', 'created_by', 'updated_by')
    search_fields = ('text', 'question__text')

    def created_at_formatted(self, obj):
        return format_datetime(obj.created_at)
    created_at_formatted.short_description = 'تاریخ ایجاد'

    def updated_at_formatted(self, obj):
        return format_datetime(obj.updated_at)
    updated_at_formatted.short_description = 'تاریخ به‌روزرسانی'


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    list_filter = ('name',)


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ('user', 'login_time_formatted', 'logout_time_formatted')
    search_fields = ('user__username',)

    def login_time_formatted(self, obj):
        return format_datetime(obj.login_time)
    login_time_formatted.short_description = 'زمان ورود'

    def logout_time_formatted(self, obj):
        return format_datetime(obj.logout_time)
    logout_time_formatted.short_description = 'زمان خروج'
