from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path("select2/", include("django_select2.urls")),
    path("ckeditor5/", include('django_ckeditor_5.urls')),
    path('api/v1/', include('core.api_urls')),  
]

# تنظیمات برای رسانه‌ها و فایل‌های استاتیک
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)