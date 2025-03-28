from django.contrib import admin
from django_jalali.admin.filters import JDateFieldListFilter
from django_jalali.admin.widgets import AdminJalaliDateWidget, AdminSplitJalaliDateTime
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
import jdatetime
from django.utils import timezone

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
    UserReferral,
    Payment
)

# تنظیمات عمومی پنل ادمین
admin.site.site_header = _("پنل مدیریت ECUPARS")
admin.site.site_title = _("مدیریت ECUPARS")
admin.site.index_title = _("داشبورد مدیریت")


class JalaliAdmin(admin.ModelAdmin):
    """کلاس پایه با پشتیبانی از تاریخ شمسی"""
    formfield_overrides = {
        models.DateTimeField: {'widget': AdminSplitJalaliDateTime},
        models.DateField: {'widget': AdminJalaliDateWidget},
    }

    def get_jalali_date(self, obj, field_name):
        date_value = getattr(obj, field_name)
        if date_value:
            if isinstance(date_value, timezone.datetime):
                return jdatetime.datetime.fromgregorian(datetime=date_value).strftime('%Y/%m/%d %H:%M:%S')
            return jdatetime.date.fromgregorian(date=date_value).strftime('%Y/%m/%d')
        return '-'
    get_jalali_date.short_description = 'تاریخ'


class BaseAdmin(JalaliAdmin):
    """کلاس پایه برای مدل‌های دارای created_at و updated_at"""
    list_display = ('__str__', 'get_jalali_created', 'get_jalali_updated')
    readonly_fields = ('get_jalali_created', 'get_jalali_updated')
    
    def get_jalali_created(self, obj):
        return self.get_jalali_date(obj, 'created_at')
    get_jalali_created.short_description = _('تاریخ ایجاد')
    get_jalali_created.admin_order_field = 'created_at'
    
    def get_jalali_updated(self, obj):
        return self.get_jalali_date(obj, 'updated_at')
    get_jalali_updated.short_description = _('تاریخ بروزرسانی')
    get_jalali_updated.admin_order_field = 'updated_at'


# --- مدل CustomUser ---
@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin, JalaliAdmin):
    list_display = ('username', 'email', 'phone_number', 'first_name', 'last_name',
                   'national_id', 'role', 'is_active', 'get_jalali_date_joined')
    list_filter = ('role', 'is_active', 'is_staff', 'is_superuser')
    search_fields = ('username', 'email', 'phone_number', 'first_name', 'last_name', 'national_id')
    ordering = ('-date_joined',)
    filter_horizontal = ('groups', 'user_permissions',)
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('اطلاعات شخصی'), {'fields': ('first_name', 'last_name', 'email', 'phone_number', 'national_id')}),
        (_('اطلاعات تکمیلی'), {'fields': ('role', 'city', 'car_brand', 'job')}),
        (_('دسترسی‌ها'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('تاریخ‌های مهم'), {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'email', 'phone_number'),
        }),
    )
    
    def get_jalali_date_joined(self, obj):
        return self.get_jalali_date(obj, 'date_joined')
    get_jalali_date_joined.short_description = _('تاریخ عضویت')
    get_jalali_date_joined.admin_order_field = 'date_joined'


# --- مدل‌های سیستم احراز هویت ---
@admin.register(LoginSession)
class LoginSessionAdmin(JalaliAdmin):
    list_display = ('user', 'session_id', 'ip_address', 'is_verified', 'get_jalali_created')
    list_filter = ('is_verified', ('created_at', JDateFieldListFilter))
    search_fields = ('user__username', 'session_id', 'ip_address')
    
    def get_jalali_created(self, obj):
        return self.get_jalali_date(obj, 'created_at')
    get_jalali_created.short_description = _('تاریخ ایجاد')


# --- مدل‌های محتوای آموزشی ---
@admin.register(IssueCategory)
class IssueCategoryAdmin(BaseAdmin):
    list_display = ('name', 'created_by', 'get_jalali_created', 'get_jalali_updated')
    search_fields = ('name',)
    list_filter = (('created_at', JDateFieldListFilter),)


@admin.register(MapCategory)
class MapCategoryAdmin(BaseAdmin):
    list_display = ('name', 'get_jalali_created', 'get_jalali_updated')
    search_fields = ('name',)
    list_filter = (('created_at', JDateFieldListFilter),)


@admin.register(Issue)
class IssueAdmin(BaseAdmin):
    list_display = ('title', 'category', 'created_by', 'get_jalali_created', 'get_jalali_updated')
    search_fields = ('title', 'description')
    list_filter = ('category', ('created_at', JDateFieldListFilter))


@admin.register(Solution)
class SolutionAdmin(BaseAdmin):
    list_display = ('title', 'is_public', 'created_by', 'get_jalali_created', 'get_jalali_updated')
    search_fields = ('title', 'content')
    list_filter = ('is_public', ('created_at', JDateFieldListFilter))


@admin.register(Map)
class MapAdmin(BaseAdmin):
    list_display = ('title', 'category', 'created_by', 'get_jalali_created', 'get_jalali_updated')
    search_fields = ('title', 'description')
    list_filter = ('category', ('created_at', JDateFieldListFilter))


@admin.register(DiagnosticStep)
class DiagnosticStepAdmin(BaseAdmin):
    list_display = ('issue', 'letter', 'created_by', 'get_jalali_created', 'get_jalali_updated')
    search_fields = ('issue__title', 'description')
    list_filter = ('issue', ('created_at', JDateFieldListFilter))


# --- مدل‌های اشتراک و پرداخت ---
@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(JalaliAdmin):
    list_display = ('name', 'price', 'duration_days', 'access_to_all_categories', 'get_jalali_created')
    list_filter = ('access_to_all_categories', ('created_at', JDateFieldListFilter))
    search_fields = ('name',)


@admin.register(UserSubscription)
class UserSubscriptionAdmin(JalaliAdmin):
    list_display = ('user', 'plan', 'get_jalali_start_date', 'get_jalali_end_date', 'is_active')
    list_filter = ('plan', 'is_active', ('start_date', JDateFieldListFilter))
    search_fields = ('user__username',)
    
    def get_jalali_start_date(self, obj):
        return self.get_jalali_date(obj, 'start_date')
    get_jalali_start_date.short_description = _('تاریخ شروع')
    
    def get_jalali_end_date(self, obj):
        return self.get_jalali_date(obj, 'end_date')
    get_jalali_end_date.short_description = _('تاریخ پایان')


@admin.register(Payment)
class PaymentAdmin(JalaliAdmin):
    list_display = ('id', 'user', 'amount', 'status', 'get_jalali_created')
    list_filter = ('status', ('created_at', JDateFieldListFilter))
    search_fields = ('user__username', 'authority')
    
    def get_jalali_created(self, obj):
        return self.get_jalali_date(obj, 'created_at')
    get_jalali_created.short_description = _('تاریخ پرداخت')


@admin.register(DiscountCode)
class DiscountCodeAdmin(JalaliAdmin):
    list_display = ('code', 'user', 'discount_percentage', 'max_usage', 'usage_count', 'get_jalali_expiration_date')
    list_filter = ('discount_percentage', ('expiration_date', JDateFieldListFilter))
    search_fields = ('code', 'user__username')
    
    def get_jalali_expiration_date(self, obj):
        return self.get_jalali_date(obj, 'expiration_date')
    get_jalali_expiration_date.short_description = _('تاریخ انقضا')


# --- مدل‌های سیستم ارجاع ---
@admin.register(ReferralCode)
class ReferralCodeAdmin(JalaliAdmin):
    list_display = ('code', 'user', 'get_jalali_created')
    search_fields = ('code', 'user__username')
    list_filter = (('created_at', JDateFieldListFilter),)


@admin.register(UserReferral)
class UserReferralAdmin(JalaliAdmin):
    list_display = ('referrer', 'referred_user', 'get_jalali_created')
    search_fields = ('referrer__username', 'referred_user__username')
    list_filter = (('created_at', JDateFieldListFilter),)


# --- سایر مدل‌ها ---
@admin.register(Bookmark)
class BookmarkAdmin(JalaliAdmin):
    list_display = ('user', 'content_object', 'get_jalali_created')
    search_fields = ('user__username',)
    list_filter = (('created_at', JDateFieldListFilter),)


@admin.register(UserActivity)
class UserActivityAdmin(JalaliAdmin):
    list_display = ('user', 'get_jalali_login_time', 'get_jalali_logout_time', 'ip_address')
    search_fields = ('user__username', 'ip_address')
    list_filter = (('login_time', JDateFieldListFilter),)
    
    def get_jalali_login_time(self, obj):
        return self.get_jalali_date(obj, 'login_time')
    get_jalali_login_time.short_description = _('زمان ورود')
    
    def get_jalali_logout_time(self, obj):
        return self.get_jalali_date(obj, 'logout_time')
    get_jalali_logout_time.short_description = _('زمان خروج')


@admin.register(ChatSession)
class ChatSessionAdmin(JalaliAdmin):
    list_display = ('user', 'consultant', 'is_active', 'get_jalali_created')
    list_filter = ('is_active', ('created_at', JDateFieldListFilter))
    search_fields = ('user__username', 'consultant__username')


@admin.register(Message)
class MessageAdmin(JalaliAdmin):
    list_display = ('session', 'sender', 'get_jalali_timestamp', 'is_read')
    list_filter = ('is_read', ('timestamp', JDateFieldListFilter))
    search_fields = ('content',)
    
    def get_jalali_timestamp(self, obj):
        return self.get_jalali_date(obj, 'timestamp')
    get_jalali_timestamp.short_description = _('زمان ارسال')


@admin.register(Article)
class ArticleAdmin(BaseAdmin):
    list_display = ('title', 'author', 'get_jalali_created', 'get_jalali_updated')
    search_fields = ('title', 'content')
    prepopulated_fields = {'slug': ('title',)}
    list_filter = (('created_at', JDateFieldListFilter),)


@admin.register(Advertisement)
class AdvertisementAdmin(JalaliAdmin):
    list_display = ('title', 'is_active', 'get_jalali_start_date', 'get_jalali_end_date')
    list_filter = ('is_active', ('start_date', JDateFieldListFilter))
    
    def get_jalali_start_date(self, obj):
        return self.get_jalali_date(obj, 'start_date')
    get_jalali_start_date.short_description = _('تاریخ شروع')
    
    def get_jalali_end_date(self, obj):
        return self.get_jalali_date(obj, 'end_date')
    get_jalali_end_date.short_description = _('تاریخ پایان')


@admin.register(Tag)
class TagAdmin(JalaliAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    list_filter = ('name',)


@admin.register(Question)
class QuestionAdmin(BaseAdmin):
    list_display = ('text', 'get_jalali_created', 'get_jalali_updated', 'created_by', 'updated_by')
    search_fields = ('text',)


@admin.register(Option)
class OptionAdmin(BaseAdmin):
    list_display = ('text', 'question', 'get_jalali_created', 'get_jalali_updated', 'created_by', 'updated_by')
    search_fields = ('text', 'question__text')


@admin.register(Subscription)
class SubscriptionAdmin(JalaliAdmin):
    list_display = ('user', 'access_level', 'active', 'get_jalali_expiry_date', 'status_display')
    search_fields = ('user__username',)
    list_filter = (('expiry_date', JDateFieldListFilter),)
    
    def get_jalali_expiry_date(self, obj):
        return self.get_jalali_date(obj, 'expiry_date')
    get_jalali_expiry_date.short_description = _('تاریخ انقضا')
    
    def status_display(self, obj):
        return "فعال" if obj.is_active() else "غیرفعال"
    status_display.short_description = 'وضعیت'