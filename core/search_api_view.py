from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from .forms import SearchForm
from .serializer import SearchResultSerializer, IssueCategorySerializer, IssueSerializer, SolutionSerializer, TagSerializer
from .models import Option, Question, DiagnosticStep, Map, Article, IssueCategory, Issue, Tag, Solution
from django.db.models import Q, Prefetch  # برای جستجوی ترکیبی
from rest_framework.pagination import PageNumberPagination



class DiagnosticPagination(PageNumberPagination):
    page_size = 10
    max_page_size = 100


    
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
            category__in=allowed_categories
        ).filter(
            Q(title__icontains=query) | 
            Q(description__icontains=query) | 
            Q(tags__name__icontains=query)  # جستجو در تگ‌ها
        ).distinct()

        cars = IssueCategory.objects.filter(
            parent_category__isnull=True,
            name__icontains=query,
            id__in=allowed_categories
        )

        tags = Tag.objects.filter(name__icontains=query)

        # Include solutions if the user has access
        if subscription.plan.access_to_diagnostic_steps:
            solutions = Solution.objects.filter(
                issues__category__in=allowed_categories
            ).filter(
                Q(title__icontains=query) | 
                Q(description__icontains=query) | 
                Q(tags__name__icontains=query)  # جستجو در تگ‌ها
            ).distinct()
        else:
            solutions = Solution.objects.none()

        # Search for maps and articles
        maps = Map.objects.filter(
            category__in=allowed_categories
        ).filter(
            Q(title__icontains=query) | 
            Q(tags__name__icontains=query)  # جستجو در تگ‌ها
        ).distinct()

        articles = Article.objects.filter(
            category__in=allowed_categories
        ).filter(
            Q(title__icontains=query) | 
            Q(content__icontains=query) | 
            Q(tags__name__icontains=query)  # جستجو در تگ‌ها
        ).distinct()

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
                diagnostic_step = DiagnosticStep.objects.filter(solution_id=solution.id).first()
                print(f"Solution ID: {solution.id}, Diagnostic Step: {diagnostic_step}")
                if diagnostic_step:
                    step_id = diagnostic_step.id
                else:
                    step_id = None  # یا مقدار پیش‌فرض دیگری که مناسب باشد
                print(step_id)
                
                unique_results.append({
                    "id": solution.id,
                    "type": "solution",
                    "data": {
                        "step_id": step_id,
                        "solution": solution
                    }
                })

        if 'tags' in filter_options or 'all' in filter_options:
            for tag in tags:
                associated_issues = tag.issues.filter(category__in=allowed_categories)
                associated_solutions = tag.solutions.filter(issues__category__in=allowed_categories) if subscription.plan.access_to_diagnostic_steps else []
                associated_maps = tag.maps.filter(category__in=allowed_categories)
                associated_articles = tag.article.filter(category__in=allowed_categories)

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
                for map in associated_maps:
                    unique_results.append({
                        "id": tag.id,
                        "type": "tag",
                        "data": {
                            "tag": tag,
                            "map": map,
                            "full_category_name": map.category.get_full_category_name(),
                        }
                    })
                for article in associated_articles:
                    unique_results.append({
                        "id": tag.id,
                        "type": "tag",
                        "data": {
                            "tag": tag,
                            "article": article,
                            "full_category_name": article.category.get_full_category_name(),
                        }
                    })

        if 'maps' in filter_options or 'all' in filter_options:
            unique_results.extend([{
                "id": map.id,
                "type": "map",
                "data": {"map": map}
            } for map in maps])

        if 'articles' in filter_options or 'all' in filter_options:
            unique_results.extend([{
                "id": article.id,
                "type": "article",
                "data": {"article": article}
            } for article in articles])

        # Serialize the results
        serializer = SearchResultSerializer(unique_results, many=True)
        return Response({'results': serializer.data})



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
        if not subscription or not subscription.is_active():
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
            results.extend(self.serialize_solutions(solutions))

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