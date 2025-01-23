from django.test import TestCase
from django.urls import reverse
from django.core.files.base import ContentFile
from core.models import Issue, IssueCategory, Solution, Tag, CustomUser, SubscriptionPlan, UserSubscription
from rest_framework_simplejwt.tokens import RefreshToken

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from core.models import IssueCategory, Issue, Solution, Tag
from core.serializers import SearchResultSerializer

class SearchAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        query = request.data.get('query', '')
        filters = request.data.get('filters', {})
        filter_options = request.data.get('filter_options', ['all'])  # دریافت فیلتر آپشن‌ها
        category_ids = filters.get('categories', [])  # دریافت دسته‌بندی‌ها
        subcategory_ids = filters.get('subcategories', [])  # دریافت زیردسته‌بندی‌ها

        # بررسی دسترسی کاربر
        user = request.user
        subscription = getattr(user, 'subscription', None)

        if not subscription:
            return Response({'results': []})

        # دسته‌بندی‌هایی که کاربر به آن‌ها دسترسی دارد
        if subscription.plan.access_to_all_categories:
            allowed_categories = IssueCategory.objects.all()
        else:
            allowed_categories = subscription.plan.restricted_categories.all()

        # اگر دسته‌بندی‌های خاص مشخص شده باشند
        if category_ids:
            allowed_categories = allowed_categories.filter(id__in=category_ids)

        # اگر زیردسته‌بندی‌های خاص مشخص شده باشند
        if subcategory_ids:
            allowed_categories = allowed_categories.filter(id__in=subcategory_ids)

        # جستجو در مدل‌های مختلف بر اساس فیلتر و دسترسی کاربر
        results = []

        if 'all' in filter_options or 'issues' in filter_options:
            issues = Issue.objects.filter(category__in=allowed_categories, title__icontains=query) | \
                     Issue.objects.filter(category__in=allowed_categories, description__icontains=query)
            for issue in issues:
                results.append({
                    "id": issue.id,
                    "type": "Error",
                    "icon_url": issue.category.logo.url if issue.category.logo else None,
                    "path": issue.category.get_full_category_name(),
                    "title": issue.title,
                    "description": issue.description
                })

        if 'all' in filter_options or 'solutions' in filter_options:
            solutions = Solution.objects.filter(issues__category__in=allowed_categories, title__icontains=query) | \
                        Solution.objects.filter(issues__category__in=allowed_categories, description__icontains=query)
            for solution in solutions:
                for issue in solution.issues.filter(category__in=allowed_categories):
                    results.append({
                        "id": solution.id,
                        "type": "Solution",
                        "icon_url": issue.category.logo.url if issue.category.logo else None,
                        "path": issue.category.get_full_category_name(),
                        "title": solution.title,
                        "description": solution.description
                    })

        if 'all' in filter_options or 'tags' in filter_options:
            tags = Tag.objects.filter(name__icontains=query)
            for tag in tags:
                associated_issues = tag.issues.filter(category__in=allowed_categories)
                for issue in associated_issues:
                    results.append({
                        "id": tag.id,
                        "type": "Tag",
                        "icon_url": issue.category.logo.url if issue.category.logo else None,
                        "path": issue.category.get_full_category_name(),
                        "title": tag.name,
                        "description": f"Tag: {tag.name}"
                    })

        return Response({'results': results})