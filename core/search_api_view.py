from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from .forms import SearchForm
from .serializer import SearchResultSerializer, IssueCategorySerializer, IssueSerializer, SolutionSerializer, TagSerializer
from .models import Option, Question, DiagnosticStep, Map, Article, IssueCategory, Issue, Tag, Solution
from django.db.models import Q, Prefetch  # برای جستجوی ترکیبی
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import BasePermission
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import status
import logging

logger = logging.getLogger(__name__)





class HasSearchPermission(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not user.is_authenticated:
            return False
            
        try:
            subscription = user.subscription
            if not subscription.is_currently_active():
                return False
                
            plan = subscription.plan
            filter_options = request.GET.getlist('filter_option', ['all'])
            
            # کاربران همیشه می‌توانند در دسته‌های با دسترسی کامل جستجو کنند
            if any(plan.full_access_categories.all()):
                return True
                
            # بررسی دسترسی عمومی
            if 'issues' in filter_options and not plan.access_to_issues:
                return False
            if 'solutions' in filter_options and not plan.access_to_diagnostic_steps:
                return False
            if 'maps' in filter_options and not plan.access_to_maps:
                return False
                
            return True
            
        except ObjectDoesNotExist:
            return False
        


class DiagnosticPagination(PageNumberPagination):
    page_size = 10
    max_page_size = 100


    
class SearchAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            # Validate and process search parameters
            query = request.GET.get('query', '').strip()
            if len(query) < 2:
                return Response(
                    {'error': 'حداقل طول جستجو ۲ کاراکتر است'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get filter options and category filters
            filter_options = request.GET.getlist('filter_option', ['all'])
            category_ids = list(map(int, request.GET.getlist('category_id', [])))
            subcategory_ids = list(map(int, request.GET.getlist('subcategory_id', [])))

            # Validate user subscription
            user = request.user
            if not hasattr(user, 'subscription'):
                return Response(
                    {'error': 'اشتراک یافت نشد'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
                
            subscription = user.subscription
            if not subscription.is_currently_active():
                return Response(
                    {'error': 'اشتراک غیرفعال است'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
                
            plan = subscription.plan

            # Get allowed categories based on user's plan
            allowed_categories = self.get_allowed_categories(
                plan, 
                category_ids, 
                subcategory_ids
            )

            # Perform search based on filter options
            results = self.perform_search(
                query, 
                filter_options, 
                plan, 
                allowed_categories
            )

            return Response({
                'count': len(results),
                'results': SearchResultSerializer(results, many=True).data
            })

        except Exception as e:
            logger.error(f"Search error: {str(e)}", exc_info=True)
            return Response(
                {'error': 'خطا در پردازش جستجو'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def get_allowed_categories(self, plan, category_ids, subcategory_ids):
        """Get all categories that user has access to based on their plan"""
        # Get full access and restricted categories
        full_access_ids = set(plan.full_access_categories.values_list('id', flat=True))
        restricted_ids = set(plan.restricted_categories.values_list('id', flat=True))

        # Base categories based on plan access
        if plan.access_to_all_categories:
            base_categories = IssueCategory.objects.exclude(id__in=restricted_ids)
        else:
            base_categories = IssueCategory.objects.none()

        # Apply user filters if provided
        if category_ids:
            base_categories = base_categories.filter(id__in=category_ids)
        if subcategory_ids:
            base_categories = base_categories.filter(id__in=subcategory_ids)

        # Get all subcategories recursively
        def get_all_subcategories(category):
            subcategories = list(IssueCategory.objects.filter(parent_category=category))
            for subcategory in subcategories:
                subcategories.extend(get_all_subcategories(subcategory))
            return subcategories

        allowed_category_ids = set(base_categories.values_list('id', flat=True))
        for category in base_categories:
            subcategories = get_all_subcategories(category)
            allowed_category_ids.update([sub.id for sub in subcategories])

        # Remove restricted categories and return final queryset
        allowed_category_ids -= restricted_ids
        return IssueCategory.objects.filter(id__in=allowed_category_ids)

    def perform_search(self, query, filter_options, plan, allowed_categories):
        """Perform search across different models based on filter options"""
        results = []
        search_query = Q(title__icontains=query)
        full_access_ids = set(plan.full_access_categories.values_list('id', flat=True))

        # Search in Issues
        if 'issues' in filter_options or 'all' in filter_options:
            if plan.access_to_issues or full_access_ids:
                issues = Issue.objects.filter(
                    (Q(category__in=full_access_ids) | Q(category__in=allowed_categories)),
                    Q(title__icontains=query) | Q(description__icontains=query)| Q(tags__name__icontains=query)
                ).distinct()
                results.extend(self.build_issue_results(issues))

        # Search in Solutions
        if ('solutions' in filter_options or 'all' in filter_options) and plan.access_to_diagnostic_steps:
            solutions = Solution.objects.filter(
                (Q(issues__category__in=full_access_ids) | 
                Q(issues__category__in=allowed_categories) |
                Q(issues__isnull=True)),
                Q(title__icontains=query) | Q(description__icontains=query) | Q(tags__name__icontains=query)
            ).distinct()
            results.extend(self.build_solution_results(solutions, allowed_categories))


        # Search in Maps
        if ('maps' in filter_options or 'all' in filter_options) and plan.access_to_maps:
            maps = Map.objects.filter(
                (Q(category__in=full_access_ids) | Q(category__in=allowed_categories)),
                Q(title__icontains=query)| Q(tags__name__icontains=query)
            ).distinct()
            results.extend(self.build_map_results(maps))

        # Search in Articles
        if 'articles' in filter_options or 'all' in filter_options:
            articles = Article.objects.filter(
                (Q(category__in=full_access_ids) | Q(category__in=allowed_categories)),
                Q(title__icontains=query) | Q(content__icontains=query)| Q(tags__name__icontains=query)
            ).distinct()
            results.extend(self.build_article_results(articles))

        return results

    def build_issue_results(self, issues):
        return [{
            'id': issue.id,
            'type': 'issue',
            'data': {
                'issue': issue,  # ارسال مستقیم شیء مدل
                'full_category_name': issue.category.get_full_category_name()
            }
        } for issue in issues]

    def build_solution_results(self, solutions, allowed_categories):
        results = []
        for solution in solutions:
            diagnostic_step = DiagnosticStep.objects.filter(
                solution_id=solution.id
            ).first()
            
            for issue in solution.issues.filter(category__in=allowed_categories):
                results.append({
                    'id': solution.id,
                    'type': 'solution',
                    'data': {
                        'step_id': diagnostic_step.id if diagnostic_step else None,
                        'solution': solution,  # ارسال مستقیم شیء مدل
                        'issue': issue,  # ارسال مستقیم شیء مدل
                        'full_category_name': issue.category.get_full_category_name()
                    }
                })
        return results

    def build_map_results(self, maps):
        return [{
            'id': map.id,
            'type': 'map',
            'data': {
                'map': map,  # ارسال مستقیم شیء مدل
                'full_category_name': map.category.get_full_category_name()
            }
        } for map in maps]

    def build_article_results(self, articles):
        return [{
            'id': article.id,
            'type': 'article',
            'data': {
                'article': article,
                'full_category_name': article.category.get_full_category_name()
            }
        } for article in articles]
    





class UnifiedSearchAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    pagination_class = PageNumberPagination


    def get_target_type(self, option):
        """تعیین نوع هدف بر اساس فیلدهای مرتبط"""
        if option.next_step:
            return "step"
        if option.issue:
            return "issue"
        if option.article:
            return "article"
        return None

    def get_target_id(self, option):
        """دریافت شناسه متناسب با نوع هدف"""
        if option.next_step:
            return option.next_step.letter
        if option.issue:
            return option.issue.id
        if option.article:
            return option.article.id
        return None
    
    
    def get(self, request):
        # دریافت پارامترهای جستجو
        query = request.GET.get('query', '')
        filter_options = request.GET.getlist('filter_option', ['all'])
        category_ids = request.GET.getlist('category_id')
        
        # بررسی دسترسی کاربر
        user = request.user
        subscription = getattr(user, 'subscription', None)
        if not subscription or not subscription.is_currently_active():
            return Response({'results': []})

        # مدیریت دسته‌بندی‌های مجاز
        if subscription.plan.access_to_all_categories:
            allowed_categories = IssueCategory.objects.all()
        else:
            allowed_categories = subscription.plan.restricted_categories.all()
        
        if category_ids:
            allowed_categories = allowed_categories.filter(id__in=category_ids)

        # ساخت کوئری‌های بهینه شده
        results = []
        
        # جستجو در Issues
        if 'issues' in filter_options or 'all' in filter_options:
            issues = Issue.objects.select_related('category')\
                .prefetch_related('tags')\
                .filter(
                    Q(category__in=allowed_categories) &
                    (Q(title__icontains=query) |
                     Q(description__icontains=query) |
                     Q(tags__name__icontains=query))
                )
            results.extend(self.serialize_issues(issues))

        # جستجو در Diagnostic Steps
        if 'steps' in filter_options or 'all' in filter_options:
            steps = DiagnosticStep.objects.select_related(
                'issue__category', 
                'question'  # لود رابطه question
            ).prefetch_related(
                Prefetch('question__options',  # استفاده از related_name صحیح
                    queryset=Option.objects.select_related(
                        'next_step', 
                        'issue', 
                        'article'
                    )
                )
            ).filter(
                Q(issue__category__in=allowed_categories) &
                Q(question__isnull=False) &  # حذف موارد بدون سوال
                (
                    Q(question__text__icontains=query) |
                    Q(issue__title__icontains=query)
                )
            )
            results.extend(self.serialize_steps(steps))

        # جستجو در Solutions
        if 'solutions' in filter_options or 'all' in filter_options:
            solutions = Solution.objects.prefetch_related('issues__category', 'tags')\
                .filter(
                    Q(issues__category__in=allowed_categories) &
                    (Q(title__icontains=query) |
                     Q(description__icontains=query) |
                     Q(tags__name__icontains=query))
                )
            results.extend(self.build_solution_results(solutions, allowed_categories))

        # جستجو در Maps
        if 'maps' in filter_options or 'all' in filter_options:
            maps = Map.objects.select_related('category')\
                .prefetch_related('tags')\
                .filter(
                    Q(category__in=allowed_categories) &
                    (Q(title__icontains=query) |
                     Q(tags__name__icontains=query))
                )
            results.extend(self.serialize_maps(maps))

        # جستجو در Articles
        if 'articles' in filter_options or 'all' in filter_options:
            articles = Article.objects.select_related('category', 'author')\
                .prefetch_related('tags')\
                .filter(
                    Q(category__in=allowed_categories) &
                    (Q(title__icontains=query) |
                     Q(content__icontains=query) |
                     Q(tags__name__icontains=query))
                )
            results.extend(self.serialize_articles(articles))

        # جستجو در Tags
        if 'tags' in filter_options or 'all' in filter_options:
            tags = Tag.objects.filter(name__icontains=query)
            results.extend(self.serialize_tags(tags))

        # صفحه‌بندی و بازگشت نتیجه
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(results, request)
        serializer = SearchResultSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    # --- توابع سریالایز ---
    def serialize_issues(self, queryset):
        return [{
            'type': 'issue',
            'id': obj.id,
            'data': {
                
                'title': obj.title,
                'category': obj.category.get_full_category_name(),
                'tags': [tag.name for tag in obj.tags.all()]
            }
        } for obj in queryset]

    def serialize_steps(self, queryset):
        return [{
            "type": "step",
            "id": step.id,
            "data": {
                
                "letter": step.letter,
                "issue": {
                    "id": step.issue.id,
                    "title": step.issue.title
                },
                "question": {
                    "id": step.question.id,
                    "text": step.question.text
                },
                "options": [{
                    "text": opt.text,
                    "target_type": self.get_target_type(opt),
                    "target_id": self.get_target_id(opt)
                } for opt in step.question.options.all()]
            }
        } for step in queryset]

    def serialize_solutions(self, queryset):
        return [{
            'type': 'solution',
            'id': obj.id,
            'data': {
                
                'title': obj.title,
                'related_issues': [{
                    'id': issue.id,
                    'title': issue.title
                } for issue in obj.issues.all()]
            }
        } for obj in queryset]

    def serialize_maps(self, queryset):
        return [{
            'type': 'map',
            'id': obj.id,
            'data': {
                
                'title': obj.title,
                'image_url': obj.image.url,
                'category': obj.category.get_full_category_name()
            }
        } for obj in queryset]

    def serialize_articles(self, queryset):
        return [{
            'type': 'article',
            'id': obj.id,
            'data': {
                'title': obj.title,
                'author': obj.author.username,
                'excerpt': obj.content[:150] + "..." if obj.content else "",
                'category': obj.category.get_full_category_name()
            }
        } for obj in queryset]

    def serialize_tags(self, queryset):
        return [{
            'type': 'tag',
            'id': obj.id,
            'data': {
                'name': obj.name,
                'related_objects': self.get_tag_relations(obj)
            }
        } for obj in queryset]

    # --- توابع کمکی ---
    def get_tag_relations(self, tag):
        relations = []
        relations.extend(tag.issues.all())
        relations.extend(tag.solutions.all())
        relations.extend(tag.map_set.all())
        relations.extend(tag.article_set.all())
        
        return [{
            'type': type(obj).__name__.lower(),
            'id': obj.id,
            'title': getattr(obj, 'title', None)
        } for obj in relations]