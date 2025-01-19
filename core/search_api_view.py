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

        # Perform search logic
        if query:
            # Search in Issues
            issues = Issue.objects.filter(title__icontains=query)
            for issue in issues:
                results.append({
                    "id": issue.id,
                    "type": "Error",
                    "icon_url": issue.category.logo,  # Placeholder icon URL
                    "path": issue.category.get_full_category_name(),  # Updated to use full_category_name
                    "title": issue.title,
                    "description": issue.description,
                })

            # Search in Solutions
            solutions = Solution.objects.filter(title__icontains=query)
            for solution in solutions:
                results.append({
                    "id": solution.id,
                    "type": "solution",
                    "icon_url": solution.category.logo,  # Placeholder icon URL
                    "path": solution.category.get_full_category_name(),  # Updated to use full_category_name
                    "title": solution.title,
                    "description": solution.description,
                })

            # Search in Maps
            maps = Map.objects.filter(title__icontains=query)
            for map in maps:
                results.append({
                    "id": map.id,
                    "type": "Map",
                    "icon_url": map.category.logo,  # Placeholder icon URL
                    "path": map.category.get_full_category_name(),  # Updated to use full_category_name
                    "title": map.title,
                    "description": map.description,
                })

        logger.info(f"Search performed with query: {query} and filters: {filters}")

        return Response({"results": results}, status=status.HTTP_200_OK)
