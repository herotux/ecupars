from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

class SearchAPIView(APIView):
    authentication_classes = [JWTAuthentication]  # استفاده از JWT برای احراز هویت
    permission_classes = [IsAuthenticated]        # فقط کاربران احراز هویت شده

    def get(self, request):
        form = SearchForm(request.GET or None)
        results = []

        if form.is_valid():
            query = form.cleaned_data.get('query', '')
            filter_options = request.GET.getlist('filter_option', ['all'])

            # بررسی دسترسی کاربر
            user = request.user
            subscription = getattr(user, 'subscription', None)

            # اگر کاربر اشتراک نداشته باشد، دسترسی محدود است
            if not subscription:
                return Response({'results': []})

            # دسته‌بندی‌هایی که کاربر به آن‌ها دسترسی دارد
            if subscription.plan.access_to_all_categories:
                allowed_categories = IssueCategory.objects.all()
            else:
                allowed_categories = subscription.plan.restricted_categories.all()

            # جستجو در مدل‌های مختلف بر اساس فیلتر و دسترسی کاربر
            issues = Issue.objects.filter(category__in=allowed_categories, title__icontains=query) | \
                    Issue.objects.filter(category__in=allowed_categories, description__icontains=query)

            cars = IssueCategory.objects.filter(parent_category__isnull=True, name__icontains=query, id__in=allowed_categories)
            categories = IssueCategory.objects.filter(name__icontains=query, id__in=allowed_categories)
            tags = Tag.objects.filter(name__icontains=query)

            # اگر کاربر به مراحل عیب‌یابی دسترسی دارد، به سولوشن‌ها نیز دسترسی دارد
            if subscription.plan.access_to_diagnostic_steps:
                solutions = Solution.objects.filter(issues__category__in=allowed_categories, title__icontains=query) | \
                            Solution.objects.filter(issues__category__in=allowed_categories, description__icontains=query)
            else:
                solutions = Solution.objects.none()  # اگر دسترسی ندارد، سولوشن‌ها را خالی برگردانید

            if 'cars' in filter_options or 'all' in filter_options:
                results.extend([{'type': 'car', 'data': {'car': car}} for car in cars])

            if 'issues' in filter_options or 'all' in filter_options:
                results.extend([{'type': 'issue', 'data': {'issue': issue, 'full_category_name': issue.category.get_full_category_name()}} for issue in issues])

            if 'solutions' in filter_options or 'all' in filter_options:
                for solution in solutions:
                    for issue in solution.issues.filter(category__in=allowed_categories):
                        results.append({
                            'type': 'solution',
                            'data': {
                                'solution': solution,
                                'issue': issue,
                                'full_category_name': issue.category.get_full_category_name(),
                            }
                        })

            if 'tags' in filter_options or 'all' in filter_options:
                for tag in tags:
                    associated_issues = tag.issues.filter(category__in=allowed_categories)
                    associated_solutions = tag.solutions.filter(issues__category__in=allowed_categories) if subscription.plan.access_to_diagnostic_steps else []
                    for issue in associated_issues:
                        results.append({
                            'type': 'tag',
                            'data': {
                                'tag': tag,
                                'issue': issue,
                                'full_category_name': issue.category.get_full_category_name(),
                            }
                        })
                    for solution in associated_solutions:
                        for issue in solution.issues.filter(category__in=allowed_categories):
                            results.append({
                                'type': 'tag',
                                'data': {
                                    'tag': tag,
                                    'solution': solution,
                                    'issue': issue,
                                    'full_category_name': issue.category.get_full_category_name(),
                                }
                            })

            # حذف نتایج تکراری
            unique_results = []
            seen = set()
            for result in results:
                result_tuple = tuple(result.items())
                if result_tuple not in seen:
                    seen.add(result_tuple)
                    unique_results.append(result)

        # سریالایز کردن نتایج
        serializer = SearchResultSerializer(unique_results, many=True)
        return Response({'results': serializer.data})