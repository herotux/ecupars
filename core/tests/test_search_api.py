from django.test import TestCase
from django.urls import reverse
from django.core.files.base import ContentFile
from core.models import Issue, IssueCategory, Solution, Tag, CustomUser, SubscriptionPlan, UserSubscription
from rest_framework_simplejwt.tokens import RefreshToken

class SearchViewTest(TestCase):
    def setUp(self):
        # ایجاد داده‌های تست
        self.car = IssueCategory.objects.create(
            name="Test Car",
            parent_category=None,
            logo=ContentFile(b"logo content", name="test_car.png")
        )
        
        self.subcategory = IssueCategory.objects.create(
            name="Test Subcategory",
            parent_category=self.car
        )
        
        self.issue = Issue.objects.create(
            title="Test Issue",
            description="Test issue description",
            category=self.subcategory
        )
        
        self.solution = Solution.objects.create(
            title="Test Solution",
            description="Test solution description"
        )
        self.solution.issues.add(self.issue)
        
        self.tag = Tag.objects.create(name="Test Tag")
        self.tag.issues.add(self.issue)
        self.tag.solutions.add(self.solution)

        # ایجاد کاربر و توکن JWT
        self.user = CustomUser.objects.create_user(
            username="testuser",
            password="testpassword"
        )

        # ایجاد اشتراک برای کاربر
        self.plan = SubscriptionPlan.objects.create(
            name="Test Plan",
            access_to_all_categories=True,
            access_to_diagnostic_steps=True
        )
        self.subscription = UserSubscription.objects.create(
            user=self.user,
            plan=self.plan
        )

        # دریافت توکن JWT برای کاربر
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)

    def get_authenticated_client(self):
        # ایجاد کلاینت احراز هویت شده با توکن JWT
        client = self.client
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        return client

    def test_all_filter(self):
        client = self.get_authenticated_client()
        response = client.get(reverse('search-api'), {
            'query': 'Test',
            'filter_option': 'all'
        })
        results = response.data['results']
        
        # بررسی وجود همه انواع نتایج
        cars = [item['data']['car'] for item in results if item['type'] == 'car']
        issues = [item['data']['issue'] for item in results if item['type'] == 'issue']
        solutions = [item['data']['solution'] for item in results if item['type'] == 'solution']
        
        self.assertIn(self.car.id, [car['id'] for car in cars])
        self.assertIn(self.issue.id, [issue['id'] for issue in issues])
        self.assertIn(self.solution.id, [solution['id'] for solution in solutions])

    def test_cars_filter(self):
        client = self.get_authenticated_client()
        response = client.get(reverse('search-api'), {
            'query': 'Car',
            'filter_option': 'cars'
        })
        results = response.data['results']
        
        cars = [item['data']['car'] for item in results if item['type'] == 'car']
        self.assertEqual([car['id'] for car in cars], [self.car.id])

    def test_issues_filter(self):
        client = self.get_authenticated_client()
        response = client.get(reverse('search-api'), {
            'query': 'Issue',
            'filter_option': 'issues'
        })
        results = response.data['results']
        
        issues = [item['data']['issue'] for item in results if item['type'] == 'issue']
        self.assertEqual([issue['id'] for issue in issues], [self.issue.id])
        self.assertEqual(results[0]['data']['full_category_name'], "Test Car > Test Subcategory")

    def test_solutions_filter(self):
        client = self.get_authenticated_client()
        response = client.get(reverse('search-api'), {
            'query': 'Solution',
            'filter_option': 'solutions'
        })
        results = response.data['results']
        
        solutions = [item['data']['solution'] for item in results if item['type'] == 'solution']
        self.assertEqual([solution['id'] for solution in solutions], [self.solution.id])
        self.assertEqual(results[0]['data']['issue']['id'], self.issue.id)

    def test_tags_filter(self):
        client = self.get_authenticated_client()
        response = client.get(reverse('search-api'), {
            'query': 'Tag',
            'filter_option': 'tags'
        })
        results = response.data['results']
        
        tags = [item['data']['tag'] for item in results if item['type'] == 'tag']
        self.assertEqual([tag['id'] for tag in tags], [self.tag.id, self.tag.id])
        self.assertEqual(results[0]['data']['issue']['id'], self.issue.id)
        self.assertEqual(results[1]['data']['solution']['id'], self.solution.id)

    def test_empty_query(self):
        client = self.get_authenticated_client()
        response = client.get(reverse('search-api'), {'query': ''})
        self.assertEqual(response.data['results'], [])

    def test_invalid_filter(self):
        client = self.get_authenticated_client()
        response = client.get(reverse('search-api'), {
            'query': 'Test',
            'filter_option': 'invalid'
        })
        self.assertEqual(response.data['results'], [])

    def test_no_access_to_diagnostic_steps(self):
        # ایجاد یک کاربر بدون دسترسی به مراحل عیب‌یابی
        user_no_access = CustomUser.objects.create_user(
            username="noaccessuser",
            password="testpassword"
        )
        plan_no_access = SubscriptionPlan.objects.create(
            name="No Access Plan",
            access_to_all_categories=True,
            access_to_diagnostic_steps=False  # بدون دسترسی به مراحل عیب‌یابی
        )
        UserSubscription.objects.create(
            user=user_no_access,
            plan=plan_no_access
        )

        # دریافت توکن JWT برای کاربر بدون دسترسی
        refresh = RefreshToken.for_user(user_no_access)
        access_token_no_access = str(refresh.access_token)

        # ارسال درخواست جستجو
        client = self.client
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token_no_access}')
        response = client.get(reverse('search-api'), {
            'query': 'Test',
            'filter_option': 'solutions'
        })
        results = response.data['results']
        
        # بررسی عدم نمایش سولوشن‌ها
        self.assertEqual(results, [])