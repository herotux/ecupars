from django.contrib import admin
from django_jalali.admin import ModelAdminJalaliMixin
from django_jalali.admin.widgets import AdminJalaliDateWidget, AdminSplitJalaliDateTime
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

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


class JalaliAdmin(ModelAdminJalaliMixin, admin.ModelAdmin):
    """کلاس پایه ادمین با پشتیبانی از تاریخ شمسی"""
    formfield_overrides = {
        models.DateTimeField: {'widget': AdminSplitJalaliDateTime},
        models.DateField: {'widget': AdminJalaliDateWidget},
    }
    
    class Media:
        js = (
            'admin/js/jquery.init.js',
            'jalali_date/js/admin_jalali_date.js',
        )


class BaseAdmin(JalaliAdmin):
    """کلاس پایه برای مدل‌های دارای created_at و updated_at"""
    list_display = ('__str__', 'created_at_jalali', 'updated_at_jalali')
    readonly_fields = ('created_at_jalali', 'updated_at_jalali')
    
    def created_at_jalali(self, obj):
        return obj.created_at.strftime('%Y/%m/%d %H:%M:%S') if obj.created_at else '-'
    created_at_jalali.short_description = _('تاریخ ایجاد')
    created_at_jalali.admin_order_field = 'created_at'
    
    def updated_at_jalali(self, obj):
        return obj.updated_at.strftime('%Y/%m/%d %H:%M:%S') if obj.updated_at else '-'
    updated_at_jalali.short_description = _('تاریخ بروزرسانی')
    updated_at_jalali.admin_order_field = 'updated_at'


# --- مدل CustomUser ---
@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin, JalaliAdmin):
    list_display = ('username', 'email', 'phone_number', 'first_name', 'last_name',
                   'national_id', 'role', 'is_active', 'date_joined_jalali')
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
    
    def date_joined_jalali(self, obj):
        return obj.date_joined.strftime('%Y/%m/%d %H:%M:%S') if obj.date_joined else '-'
    date_joined_jalali.short_description = _('تاریخ عضویت')
    date_joined_jalali.admin_order_field = 'date_joined'


# --- مدل‌های سیستم احراز هویت ---
@admin.register(LoginSession)
class LoginSessionAdmin(JalaliAdmin):
    list_display = ('user', 'session_id', 'ip_address', 'is_verified', 'created_at_jalali')
    list_filter = ('is_verified',)
    search_fields = ('user__username', 'session_id', 'ip_address')
    
    def created_at_jalali(self, obj):
        return obj.created_at.strftime('%Y/%m/%d %H:%M:%S')
    created_at_jalali.short_description = _('تاریخ ایجاد')


# --- مدل‌های محتوای آموزشی ---
@admin.register(IssueCategory)
class IssueCategoryAdmin(BaseAdmin):
    list_display = ('name', 'created_by', 'created_at_jalali', 'updated_at_jalali')
    search_fields = ('name',)


@admin.register(MapCategory)
class MapCategoryAdmin(BaseAdmin):
    list_display = ('name', 'created_at_jalali', 'updated_at_jalali')
    search_fields = ('name',)


@admin.register(Issue)
class IssueAdmin(BaseAdmin):
    list_display = ('title', 'category', 'created_by', 'created_at_jalali', 'updated_at_jalali')
    search_fields = ('title', 'description')
    list_filter = ('category',)


@admin.register(Solution)
class SolutionAdmin(BaseAdmin):
    list_display = ('title', 'is_public', 'created_by', 'created_at_jalali', 'updated_at_jalali')
    search_fields = ('title', 'content')
    list_filter = ('is_public',)


@admin.register(Map)
class MapAdmin(BaseAdmin):
    list_display = ('title', 'category', 'created_by', 'created_at_jalali', 'updated_at_jalali')
    search_fields = ('title', 'description')
    list_filter = ('category',)


@admin.register(DiagnosticStep)
class DiagnosticStepAdmin(BaseAdmin):
    list_display = ('issue', 'letter', 'created_by', 'created_at_jalali', 'updated_at_jalali')
    search_fields = ('issue__title', 'description')
    list_filter = ('issue',)


# --- مدل‌های اشتراک و پرداخت ---
@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(JalaliAdmin):
    list_display = ('name', 'price', 'duration_days', 'access_to_all_categories', 'created_at_jalali')
    list_filter = ('access_to_all_categories',)
    search_fields = ('name',)


@admin.register(UserSubscription)
class UserSubscriptionAdmin(JalaliAdmin):
    list_display = ('user', 'plan', 'start_date_jalali', 'end_date_jalali', 'is_active')
    list_filter = ('plan', 'is_active')
    search_fields = ('user__username',)
    
    def start_date_jalali(self, obj):
        return obj.start_date.strftime('%Y/%m/%d')
    start_date_jalali.short_description = _('تاریخ شروع')
    
    def end_date_jalali(self, obj):
        return obj.end_date.strftime('%Y/%m/%d')
    end_date_jalali.short_description = _('تاریخ پایان')


@admin.register(Payment)
class PaymentAdmin(JalaliAdmin):
    list_display = ('id', 'user', 'amount', 'status', 'created_at_jalali')
    list_filter = ('status',)
    search_fields = ('user__username', 'authority')
    
    def created_at_jalali(self, obj):
        return obj.created_at.strftime('%Y/%m/%d %H:%M:%S')
    created_at_jalali.short_description = _('تاریخ پرداخت')


@admin.register(DiscountCode)
class DiscountCodeAdmin(JalaliAdmin):
    list_display = ('code', 'user', 'discount_percentage', 'max_usage', 'usage_count', 'expiration_date_jalali')
    list_filter = ('discount_percentage',)
    search_fields = ('code', 'user__username')
    
    def expiration_date_jalali(self, obj):
        return obj.expiration_date.strftime('%Y/%m/%d') if obj.expiration_date else '-'
    expiration_date_jalali.short_description = _('تاریخ انقضا')


# --- مدل‌های سیستم ارجاع ---
@admin.register(ReferralCode)
class ReferralCodeAdmin(JalaliAdmin):
    list_display = ('code', 'user', 'created_at_jalali')
    search_fields = ('code', 'user__username')


@admin.register(UserReferral)
class UserReferralAdmin(JalaliAdmin):
    list_display = ('referrer', 'referred_user', 'created_at_jalali')
    search_fields = ('referrer__username', 'referred_user__username')


# --- سایر مدل‌ها ---
@admin.register(Bookmark)
class BookmarkAdmin(JalaliAdmin):
    list_display = ('user', 'content_object', 'created_at_jalali')
    search_fields = ('user__username',)


@admin.register(UserActivity)
class UserActivityAdmin(JalaliAdmin):
    list_display = ('user', 'login_time_jalali', 'logout_time_jalali', 'ip_address')
    search_fields = ('user__username', 'ip_address')
    
    def login_time_jalali(self, obj):
        return obj.login_time.strftime('%Y/%m/%d %H:%M:%S') if obj.login_time else '-'
    login_time_jalali.short_description = _('زمان ورود')
    
    def logout_time_jalali(self, obj):
        return obj.logout_time.strftime('%Y/%m/%d %H:%M:%S') if obj.logout_time else '-'
    logout_time_jalali.short_description = _('زمان خروج')


@admin.register(ChatSession)
class ChatSessionAdmin(JalaliAdmin):
    list_display = ('user', 'consultant', 'is_active', 'created_at_jalali')
    list_filter = ('is_active',)
    search_fields = ('user__username', 'consultant__username')


@admin.register(Message)
class MessageAdmin(JalaliAdmin):
    list_display = ('session', 'sender', 'timestamp_jalali', 'is_read')
    list_filter = ('is_read',)
    search_fields = ('content',)
    
    def timestamp_jalali(self, obj):
        return obj.timestamp.strftime('%Y/%m/%d %H:%M:%S')
    timestamp_jalali.short_description = _('زمان ارسال')


@admin.register(Article)
class ArticleAdmin(BaseAdmin):
    list_display = ('title', 'author', 'created_at_jalali', 'updated_at_jalali')
    search_fields = ('title', 'content')
    prepopulated_fields = {'slug': ('title',)}


@admin.register(Advertisement)
class AdvertisementAdmin(JalaliAdmin):
    list_display = ('title', 'is_active', 'start_date_jalali', 'end_date_jalali')
    list_filter = ('is_active',)
    
    def start_date_jalali(self, obj):
        return obj.start_date.strftime('%Y/%m/%d') if obj.start_date else '-'
    start_date_jalali.short_description = _('تاریخ شروع')
    
    def end_date_jalali(self, obj):
        return obj.end_date.strftime('%Y/%m/%d') if obj.end_date else '-'
    end_date_jalali.short_description = _('تاریخ پایان')