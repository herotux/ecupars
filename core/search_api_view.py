from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from .forms import SearchForm
from .serializer import SearchResultSerializer, IssueCategorySerializer, IssueSerializer, SolutionSerializer, TagSerializer
from .models import IssueCategory, Issue, Tag, Solution



class SearchAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        query = request.GET.get('query', '')
        filter_options = request.GET.getlist('filter_option', ['all'])
        category_ids = request.GET.getlist('category_id')  # دریافت لیست category_idها
        subcategory_ids = request.GET.getlist('subcategory_id')  # دریافت لیست subcategory_idها

        # Check user access
        user = request.user
        subscription = getattr(user, 'subscription', None)

        if not subscription:
            return Response({'results': []})

        # Categories the user has access to
        if subscription.plan.access_to_all_categories:
            allowed_categories = IssueCategory.objects.all()
        else:
            allowed_categories = subscription.plan.restricted_categories.all()

        # Filter by categories and subcategories
        if category_ids:
            allowed_categories = allowed_categories.filter(id__in=category_ids)
        if subcategory_ids:
            allowed_categories = allowed_categories.filter(id__in=subcategory_ids)

        # Search in models based on filters and user access
        issues = Issue.objects.filter(
            category__in=allowed_categories,
            title__icontains=query
        ) | Issue.objects.filter(
            category__in=allowed_categories,
            description__icontains=query
        )

        cars = IssueCategory.objects.filter(
            parent_category__isnull=True,
            name__icontains=query,
            id__in=allowed_categories
        )

        tags = Tag.objects.filter(name__icontains=query)

        # Include solutions if the user has access
        if subscription.plan.access_to_diagnostic_steps:
            solutions = Solution.objects.filter(
                issues__category__in=allowed_categories,
                title__icontains=query
            ) | Solution.objects.filter(
                issues__category__in=allowed_categories,
                description__icontains=query
            )
        else:
            solutions = Solution.objects.none()

        # Initialize unique_results
        unique_results = []

        if 'cars' in filter_options or 'all' in filter_options:
            unique_results.extend([{
                "id": car.id,
                "type": "car",
                "data": {"car": car}
            } for car in cars])

        if 'issues' in filter_options or 'all' in filter_options:
            unique_results.extend([{
                "id": issue.id,
                "type": "issue",
                "data": {
                    "issue": issue,
                    "full_category_name": issue.category.get_full_category_name()
                }
            } for issue in issues])

        if 'solutions' in filter_options or 'all' in filter_options:
            for solution in solutions:
                for issue in solution.issues.filter(category__in=allowed_categories):
                    unique_results.append({
                        "id": solution.id,
                        "type": "solution",
                        "data": {
                            "solution": solution,
                            "issue": issue,
                            "full_category_name": issue.category.get_full_category_name(),
                        }
                    })

        if 'tags' in filter_options or 'all' in filter_options:
            for tag in tags:
                associated_issues = tag.issues.filter(category__in=allowed_categories)
                associated_solutions = tag.solutions.filter(issues__category__in=allowed_categories) if subscription.plan.access_to_diagnostic_steps else []
                for issue in associated_issues:
                    unique_results.append({
                        "id": tag.id,
                        "type": "tag",
                        "data": {
                            "tag": tag,
                            "issue": issue,
                            "full_category_name": issue.category.get_full_category_name(),
                        }
                    })
                for solution in associated_solutions:
                    for issue in solution.issues.filter(category__in=allowed_categories):
                        unique_results.append({
                            "id": tag.id,
                            "type": "tag",
                            "data": {
                                "tag": tag,
                                "solution": solution,
                                "issue": issue,
                                "full_category_name": issue.category.get_full_category_name(),
                            }
                        })

        # Serialize the results
        serializer = SearchResultSerializer(unique_results, many=True)
        return Response({'results': serializer.data})