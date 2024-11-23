from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenRefreshView


urlpatterns = [
    path('login', views.login_view, name='login'),
    path('verify_otp', views.verify_otp_view, name='verify_otp'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('cars/', views.HomeAPIView.as_view(), name='cars-list'),
]