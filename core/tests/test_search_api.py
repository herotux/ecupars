from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .models import Issue, Solution, Map, IssueCategory

class SearchAPITestCase(APITestCase):
    def setUp(self):
        # Create test data
        self.category = IssueCategory.objects.create(name="Test Category")
        self.issue = Issue.objects.create(title="Test Issue", description="Test Description", category=self.category)
        self.solution = Solution.objects.create(title="Test Solution", description="Test Solution Description")
        self.map = Map.objects.create(title="Test Map", category=self.category)

    def test_search_api(self):
        url = reverse('search-api')
        payload = {
            "query": "Test",
            "filters": {
                "categories": [self.category.id],
                "subcategories": []
            }
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertGreater(len(response.data["results"]), 0)

    def test_search_api_no_results(self):
        url = reverse('search-api')
        payload = {
            "query": "Nonexistent",
            "filters": {
                "categories": [],
                "subcategories": []
            }
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertEqual(len(response.data["results"]), 0)
