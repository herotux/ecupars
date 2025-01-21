from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Issue, Solution, Map
import logging

logger = logging.getLogger('core')

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Issue, Solution, Map
import logging

logger = logging.getLogger('core')

class SearchAPIView(APIView):
    def post(self, request):
        query = request.data.get('query', '')
        filters = request.data.get('filters', {})
        categories = filters.get('categories', [])
        subcategories = filters.get('subcategories', [])

        results = []

        # Search in Issues
        issues = Issue.objects.all()
        if query:
            issues = issues.filter(title__icontains=query) | issues.filter(description__icontains=query)
        if categories:
            issues = issues.filter(category__id__in=categories)

        for issue in issues:
            results.append({
                "id": issue.id,
                "type": "Error",
                "icon_url": issue.category.logo.url if issue.category.logo else None,  # Use .url to get the file URL
                "path": issue.category.get_full_category_name(),
                "title": issue.title,
                "description": issue.description,
            })

        # Search in Solutions
        solutions = Solution.objects.all()
        if query:
            solutions = solutions.filter(title__icontains=query) | solutions.filter(description__icontains=query)
        if categories:
            # Assuming solutions are related to issues, which are related to categories
            solutions = solutions.filter(issues__category__id__in=categories).distinct()

        for solution in solutions:
            results.append({
                "id": solution.id,
                "type": "Solution",
                "icon_url": solution.issues.first().category.logo.url if solution.issues.exists() and solution.issues.first().category.logo else None,  # Use the first issue's category logo
                "path": solution.issues.first().category.get_full_category_name() if solution.issues.exists() else None,
                "title": solution.title,
                "description": solution.description,
            })

        # Search in Maps
        maps = Map.objects.all()
        if query:
            maps = maps.filter(title__icontains=query)
        if categories:
            maps = maps.filter(category__id__in=categories)

        for map in maps:
            results.append({
                "id": map.id,
                "type": "Map",
                "icon_url": map.category.logo.url if map.category.logo else None,  # Use .url to get the file URL
                "path": map.category.get_full_category_name(),
                "title": map.title,
                "description": map.description,
            })

        logger.info(f"Search performed with query: {query}, filters: {filters}, and returned {len(results)} results.")

        return Response({"results": results}, status=status.HTTP_200_OK)