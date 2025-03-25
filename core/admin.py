from django.contrib import admin
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

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
    UserSubscription,
    SubscriptionPlan,
    Advertisement,
    ChatSession,
    Message,
    Article,
    DiscountCode,
    ReferralCode,
    UserReferral

)

# تنظیمات عمومی پنل ادمین
admin.site.site_header = _("ECUPARS")
admin.site.site_title = _("ECUPARS")
admin.site.index_title = _("ECUPARS")


def format_datetime(value):
    if value:
        return timezone.localtime(value).strftime('%Y-%m-%d %H:%M:%S')
    return ''


class BaseAdmin(admin.ModelAdmin):
    """یک کلاس پایه برای اضافه کردن متدهای مشترک"""
    def created_at_formatted(self, obj):
        return format_datetime(obj.created_at)
    created_at_formatted.short_description = 'تاریخ ایجاد'

    def updated_at_formatted(self, obj):
        return format_datetime(obj.updated_at)
    updated_at_formatted.short_description = 'تاریخ بروزرسانی'


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'role', 'national_id','car_brand', 'city', 'job', 'phone_number')
    search_fields = ('username', 'email', 'national_id', 'phone_number')
    list_filter = ('role',)


@admin.register(LoginSession)
class LoginSessionAdmin(BaseAdmin):
    list_display = ('user', 'session_id', 'is_verified', 'created_at_formatted')
    search_fields = ('user__username', 'session_id')


@admin.register(IssueCategory)
class IssueCategoryAdmin(BaseAdmin):
    list_display = ('name', 'created_at_formatted', 'updated_at_formatted', 'created_by', 'updated_by')
    search_fields = ('name',)


@admin.register(MapCategory)
class MapCategoryAdmin(BaseAdmin):
    list_display = ('name', 'created_at_formatted', 'updated_at_formatted')
    search_fields = ('name',)


@admin.register(Issue)
class IssueAdmin(BaseAdmin):
    list_display = ('title', 'category', 'created_at_formatted', 'updated_at_formatted', 'created_by', 'updated_by')
    search_fields = ('title',)


@admin.register(Solution)
class SolutionAdmin(BaseAdmin):
    list_display = ('title', 'is_public', 'created_at_formatted', 'updated_at_formatted', 'created_by', 'updated_by')
    search_fields = ('title',)


@admin.register(Map)
class MapAdmin(BaseAdmin):
    list_display = ('title', 'category', 'created_at_formatted', 'updated_at_formatted', 'created_by', 'updated_by')
    search_fields = ('title',)


@admin.register(DiagnosticStep)
class DiagnosticStepAdmin(BaseAdmin):
    list_display = ('issue', 'letter', 'created_at_formatted', 'updated_at_formatted', 'created_by', 'updated_by')
    search_fields = ('issue__title',)


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'access_level', 'active', 'expiry_date', 'status_display')
    search_fields = ('user__username',)

    def status_display(self, obj):
        return "فعال" if obj.is_active() else "غیرفعال"
    status_display.short_description = 'وضعیت'


@admin.register(Bookmark)
class BookmarkAdmin(BaseAdmin):
    list_display = ('user', 'title', 'created_at_formatted')
    search_fields = ('user__username', 'title')


@admin.register(Question)
class QuestionAdmin(BaseAdmin):
    list_display = ('text', 'created_at_formatted', 'updated_at_formatted', 'created_by', 'updated_by')
    search_fields = ('text',)


@admin.register(Option)
class OptionAdmin(BaseAdmin):
    list_display = ('text', 'question', 'created_at_formatted', 'updated_at_formatted', 'created_by', 'updated_by')
    search_fields = ('text', 'question__text')


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


@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'start_date', 'end_date', 'is_active_display')
    search_fields = ('user__username', 'plan__name')

    def is_active_display(self, obj):
        return "فعال" if obj.is_active() else "غیرفعال"
    is_active_display.short_description = 'وضعیت'


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'access_to_all_categories', 'access_to_diagnostic_steps')
    search_fields = ('name',)
    list_filter = ('access_to_all_categories', 'access_to_diagnostic_steps')


@admin.register(Advertisement)
class AdvertisementAdmin(admin.ModelAdmin):
    list_display = ('title', 'link', 'created_at')


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'consultant', 'is_active', 'created_at')
    list_filter = ('is_active',)

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'session', 'sender', 'timestamp')




@admin.register(Article)
class ArticleAdmin(BaseAdmin):
    list_display = ('title', 'content', 'created_at_formatted', 'updated_at_formatted')
    search_fields = ('title',)




@admin.register(ReferralCode)
class ReferralCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'user')
    autocomplete_fields = ['user']
   



@admin.register(DiscountCode)
class DiscountCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_percentage', 'created_at')
    autocomplete_fields = ['user']
    


@admin.register(UserReferral)
class UserReferralAdmin(admin.ModelAdmin):
    list_display = ('referrer', 'referred_user', 'created_at')