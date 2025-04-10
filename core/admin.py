from django.contrib import admin
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.admin import UserAdmin






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
class CustomUserAdmin(UserAdmin):
    list_display = ('id', 'username', 'role', 'date_joined', 'first_name', 
                   'last_name', 'car_brand', 'city', 'job', 'phone_number', 'is_staff')
    
    search_fields = ('username', 'first_name', 'last_name', 'phone_number')
    
    list_filter = (
        'role',
        'is_staff',
        'is_superuser',
        'is_active',
        ('date_joined'),  # فیلتر تاریخ شمسی
    )

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('اطلاعات شخصی', {'fields': ('first_name', 'last_name', 'email', 'national_id', 'phone_number')}),
        ('اطلاعات اضافی', {'fields': ('role', 'car_brand', 'city', 'job')}),
        ('دسترسی‌ها', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('تاریخ‌های مهم', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'email', 'first_name', 'last_name'),
        }),
    )


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
        return "فعال" if obj.is_currently_active() else "غیرفعال"
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
    autocomplete_fields = ['user']

    def is_active_display(self, obj):
        return "فعال" if obj.is_currently_active() else "غیرفعال"
    is_active_display.short_description = 'وضعیت'


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'duration_days', 'access_to_all_categories', 
                   'access_to_diagnostic_steps', 'access_to_maps', 'access_to_issues')
    search_fields = ('name', 'description')
    list_filter = ('access_to_all_categories', 'access_to_diagnostic_steps',
                  'access_to_maps', 'access_to_issues')
    list_per_page = 20
    autocomplete_fields = ('restricted_categories', 'full_access_categories')
    
    fieldsets = (
        ('اطلاعات پایه', {
            'fields': ('name', 'description', 'price', 'duration_days')
        }),
        ('تنظیمات دسترسی', {
            'fields': (
                'access_to_all_categories',
                'access_to_diagnostic_steps',
                'access_to_maps',
                'access_to_issues'
            )
        }),
        ('مدیریت دسته‌بندی‌ها', {
            'classes': ('collapse',),
            'fields': ('restricted_categories', 'full_access_categories')
        }),
    )
    
    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)
        try:
            price = int(search_term)
            queryset |= self.model.objects.filter(price=price)
        except ValueError:
            pass
        return queryset, use_distinct


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


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'amount', 'status',  'created_at')
