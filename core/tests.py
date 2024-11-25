from rest_framework.test import APITestCase
from rest_framework import status
from core.models import IssueCategory
from core.models import CustomUser  # وارد کردن مدل سفارشی
from rest_framework_simplejwt.tokens import RefreshToken
from django.urls import reverse
from django.test import Client


class CarAPITestCase(APITestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(username='testuser', password='testpassword')
        self.user.is_active = True
        self.user.save()
        self.refresh = RefreshToken.for_user(self.user)
        self.access_token = str(self.refresh.access_token)
        print(self.access_token)
        self.url = '/api/v1/cars/'
        # افزودن دسته‌بندی برای تست
        self.category = IssueCategory.objects.create(name="Test Category", parent_category=None)
        
        self.url = reverse('cars-list')


    


    def test_access_without_token(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('detail', response.data)

    def test_access_with_valid_token(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_access_with_invalid_token(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalidtoken123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)