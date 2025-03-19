from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Payment, Advertisement, UserActivity, MapCategory, Map, CustomUser, IssueCategory, Issue, Solution, Subscription, Bookmark, DiagnosticStep, Question, Tag, Option
from .forms import SearchForm, MapCategoryForm, MapForm, UserForm, IssueCategoryForm, IssueCatForm, CustomUserCreationForm,issue_SolutionForm, IssueForm, SolutionForm, SubscriptionForm, QuestionForm, OptionForm, DiagnosticStepForm
from .serializer import AdvertisementSerializer, MapSerializer, IssueCategorySerializer, IssueSerializer, CategorySerializer
from .models import DiscountCode, ReferralCode, SubscriptionPlan, UserSubscription
from .serializer import CustomUserSerializer, MessageSerializer, SubscriptionPlanSerializer, UserSubscriptionSerializer
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login as auth_login
from django.http import JsonResponse
from django.db import models
import json
from django.db import transaction
import time
from django.contrib.auth.views import LoginView
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.views import View
from django.utils.safestring import mark_safe
from io import StringIO
import pandas as pd
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
import logging
import random
from django.contrib.auth import authenticate
from .models import LoginSession
from .serializer import IssueSerializer, QuestionSerializer
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from rest_framework.decorators import permission_classes
from django.http import Http404
from .serializer import DiagnosticStepSerializer, OptionSerializer,ChatSessionSerializer, ArticleSerializer
from django.contrib.auth.views import LogoutView as AuthLogoutView
from django.contrib.auth import login
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone
from datetime import timedelta
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import BasePermission
from django.db import IntegrityError
from zarinpal.api import ZarinPalPayment
from django.core.exceptions import PermissionDenied
from functools import wraps
from .models import ChatSession, Message, UserChatSession
from django.contrib.auth import get_user_model
import os
from rest_framework import viewsets
from .models import Article, UserReferral  # Import the Article model
from .forms import ArticleForm  # Import the form for Article
from rest_framework.pagination import LimitOffsetPagination
from django.conf import settings
from .serializer import PaymentRequestSerializer, PaymentVerificationSerializer
from django.utils.timezone import now
from django.core.cache import cache
from rest_framework.exceptions import APIException
from .services import LimoSMSClient
import requests
from django.db.models import Q












def send_pattern_sms(otp_id, replace_tokens, mobile_number):
    url = "https://api.limosms.com/api/sendpatternmessage"
    payload = {
        "OtpId": otp_id,
        "ReplaceToken": replace_tokens,
        "MobileNumber": mobile_number
    }
    headers = {"ApiKey": settings.LIMOSMS_API_KEY}

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()  
        response_data = response.json()
        print("پاسخ سرور لیموپیامک:", response_data)


        return {
            "success": response_data.get("success", False),
            "message": response_data.get("message", "خطای نامشخص از سرور")
        }

    except requests.exceptions.HTTPError as http_err:
        print("خطای HTTP:", http_err)
        return {
            "success": False,
            "message": f"خطای سرور: {http_err}"
        }
    except Exception as e:
        print("خطای غیرمنتظره:", str(e))
        return {
            "success": False,
            "message": f"خطای ارتباطی: {str(e)}"
        }



def is_admin(user):
    # بررسی آیا کاربر لاگین کرده است
    if not user.is_authenticated:
        return False
    
    # بررسی آیا کاربر سوپریوزر است
    if user.is_superuser:
        return True
    
    # بررسی آیا کاربر دارای نقش 'admin' است
    if hasattr(user, 'role'):
        return user.role == 'admin'
    
    # اگر کاربر لاگین کرده اما نقش ندارد
    return False


@login_required
def article_list(request):
    articles = Article.objects.all()
    return render(request, 'article_list.html', {'articles': articles})

@login_required
def article_detail(request, article_id):
    article = get_object_or_404(Article, id=article_id)
    question = article.question  
    return render(request, 'article_detail.html', {'article': article,'question':question})

# @login_required
# def article_create(request):
#     if request.method == 'POST':
#         form = ArticleForm(request.POST)
#         if form.is_valid():
#             article = form.save(commit=False)
#             article.author = request.user  # Set the author to the current user
#             article.save()
#             return redirect('article_list')
#     else:
#         form = ArticleForm()
#     return render(request, 'article_form.html', {'form': form})




@user_passes_test(is_admin)
@login_required
def article_create(request, category_id):
    category = get_object_or_404(IssueCategory, id=category_id)

    if request.method == 'POST':
        form = ArticleForm(request.POST)
        if form.is_valid():
            article = form.save(commit=False)
            article.category = category  # Set the category to the selected one
            article.author = request.user  # Set the author to the current user
            article.save()  # Save the article first
            form.save()
            form.save_m2m()  # Save the many-to-many relationship for tags
            return redirect('article_list')
    else:
        form = ArticleForm()
    return render(request, 'article_form.html', {'form': form, 'category': category})

    

@login_required
def article_update(request, article_id):
    article = get_object_or_404(Article, id=article_id)
    if request.method == 'POST':
        form = ArticleForm(request.POST, instance=article)
        if form.is_valid():
            form.save()
            return redirect('article_detail', article_id=article.id)
    else:
        form = ArticleForm(instance=article)
    return render(request, 'article_form.html', {'form': form})

@login_required
def article_delete(request, article_id):
    article = get_object_or_404(Article, id=article_id)
    if request.method == 'POST':
        article.delete()
        return redirect('article_list')
    return render(request, 'article_confirm_delete.html', {'article': article})







def has_category_access(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        category_id = kwargs.get('cat_id')  # Get the category ID from URL kwargs
        user = request.user

        if not user.is_authenticated or not hasattr(user, 'subscription'):
            raise PermissionDenied("You do not have permission to access this category.")

        subscription = user.subscription

        # Check access to all categories
        if subscription.plan.access_to_all_categories:
            return view_func(request, *args, **kwargs)

        # Get the specified category
        try:
            category = IssueCategory.objects.get(id=category_id)
        except IssueCategory.DoesNotExist:
            raise PermissionDenied("The specified category does not exist.")

        # Get the ID of the specified category and all its parent categories
        parent_categories = []
        current_category = category

        # Traverse up to find all parent categories
        while current_category.parent_category is not None:
            parent_categories.append(current_category.parent_category.id)
            current_category = current_category.parent_category

        # Combine the parent categories and the current category
        category_ids = parent_categories + [category_id]
        
        # Check if the user has access to the specified category or any of its parent categories
        if not any(cat_id in subscription.active_categories.values_list('id', flat=True) for cat_id in category_ids):
            raise PermissionDenied("You do not have access to this category or its parent categories.")

        return view_func(request, *args, **kwargs)

    return _wrapped_view






def has_diagnostic_access(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        user = request.user

        if not user.is_authenticated or not hasattr(user, 'subscription'):
            raise PermissionDenied("You do not have permission to access this diagnostic step.")

        subscription = user.subscription

        # بررسی دسترسی به مراحل عیب‌یابی
        if not subscription.plan.access_to_diagnostic_steps:
            raise PermissionDenied("You do not have access to this diagnostic step.")

        return view_func(request, *args, **kwargs)

    return _wrapped_view


















logger = logging.getLogger('core')












def render_categories(categories):
    output = StringIO()

    for category in categories:
        edit_url = reverse('issue_category_update', args=[category.id])
        delete_url = reverse('issue_category_delete', args=[category.id])
        children = category.subcategories.all()  # Fetch children using related name
        cat_detail = reverse('car_detail', args=[category.id])

        # Add category item
        output.write(f'''
            <li class="list-group-item">
                <span class="category-toggle" style="cursor: pointer;">
                    + 
                </span>
                <a href="{cat_detail}" style="font-weight: bold;">{category.name}</a>  
                <span class="float-left">
                    <a href="{edit_url}" class="btn btn-warning btn-sm">
                        <i class="fa fa-edit"></i> 
                    </a>
                    <a href="{delete_url}" class="btn btn-danger btn-sm">
                        <i class="fa fa-trash"></i> 
                    </a>
                </span>
                <ul class='subcategories'>{render_categories(children)}</ul>
            </li>
        ''')

    return mark_safe(output.getvalue())



def render_mapcategories(categories):
    output = StringIO()

    for category in categories:
        edit_url = reverse('map_category_update', args=[category.id])
        delete_url = reverse('map_category_delete', args=[category.id])
        children = category.subcategories.all()  # Fetch children using related name
        mapcat_detail = reverse('mapcat_detail', args=[category.id])

        # Add category item
        output.write(f'''
            <li class="list-group-item">
                <span class="category-toggle" style="cursor: pointer;">
                    + 
                </span>
                <a href="{mapcat_detail}" style="font-weight: bold;">{category.name}</a>  
                <span class="float-left">
                    <a href="{edit_url}" class="btn btn-warning btn-sm">
                        <i class="fa fa-edit"></i> 
                    </a>
                    <a href="{delete_url}" class="btn btn-danger btn-sm">
                        <i class="fa fa-trash"></i> 
                    </a>
                </span>
                <ul class='subcategories'>{render_mapcategories(children)}</ul>
            </li>
        ''')

    return mark_safe(output.getvalue())













def check_user_in_group(user, group_name):
    try:
        group = Group.objects.get(name=group_name)
        return user.groups.filter(id=group.id).exists()
    except:
        return False


    
def is_Consultants(user): #بررسی اینکه کاربر مشاور است یا خیر
    # consultants = Group.objects.get(name=Consultants)
    return check_user_in_group(user, 'Consultants')


def is_vip(user):
    return user.role == 'premium'

def has_access(user, required_level):
    return user.access_level >= required_level


@user_passes_test(is_admin)
def admin_dashboard(request):
    issue_categories = IssueCategory.objects.all()
    page_title = "داشبورد مدیر"
    return render(request, 'admin_dashboard.html', {'issue_categories': issue_categories, 'page_title': page_title, 'user': request.user})


@login_required
def user_dashboard(request):
    # تلاش برای گرفتن اشتراک کاربر
    subscription = Subscription.objects.filter(user=request.user).first()
    page_title = "داشبورد کاربر"
    
    return render(request, 'user_dashboard.html', {'subscription': subscription, 'page_title': page_title})


@login_required
def home(request):
    page_title = "خانه"
    cars = IssueCategory.objects.filter(parent_category__isnull=True)
    issue_categoriess = IssueCategory.objects.all()
    return render(request, 'index.html', {'issue_categoriess':issue_categoriess, 'cars': cars, 'page_title': page_title})

@user_passes_test(is_admin)
@login_required
def manage_users(request):
    users = CustomUser.objects.all()
    
  
    user_last_login = {}
    for user in users:
        last_activity = UserActivity.objects.filter(user=user).order_by('-login_time').first()
        user_last_login[user.pk] = last_activity.login_time if last_activity else None
    
    page_title = "مدیریت کاربران"
    return render(request, 'manage_users.html', {'users': users, 'user_last_login': user_last_login, 'page_title': page_title})









@user_passes_test(is_admin)
@login_required
def manage_issue_categories(request):
    issue_categories = IssueCategory.objects.filter(parent_category__isnull=True)
    rendered_categories = render_categories(issue_categories)
    page_title = "مدیریت دسته ها"
    return render(request, 'manage_issue_categories.html', {'rendered_categories': rendered_categories, 'issue_categories': issue_categories, 'page_title': page_title})



@user_passes_test(is_admin)
@login_required
def issue_category_create(request):
    page_title = "ایجاد دسته "
    if request.method == 'POST':
        form = IssueCategoryForm(request.POST, request.FILES)

        if form.is_valid():
            form.save()
            return redirect('manage_issue_categories')
    else:
        form = IssueCategoryForm()
    return render(request, 'issue_category_form.html', {'form': form, 'page_title': page_title})




def add_subcategory(request):
    if request.method == 'POST':
        name = request.POST.get('subcategory_name')
        parent_category_id = request.POST.get('parent_category_id')
        parent_category = IssueCategory.objects.get(id=parent_category_id)

        new_category = IssueCategory(name=name, parent_category=parent_category, created_by=request.user)
        new_category.save()

        return JsonResponse({'status': 'success', 'message': 'زیر دسته با موفقیت اضافه شد.'})

    return JsonResponse({'status': 'error', 'message': 'درخواست نامعتبر است.'})





@user_passes_test(is_admin)
@login_required
def issue_category_update(request, category_id):
    category = get_object_or_404(IssueCategory, id=category_id)
    page_title = "ویرایش دسته"
    if request.method == 'POST':
        form = IssueCategoryForm(request.POST, request.FILES, instance=category)
        if form.is_valid():
            form.save()
            return redirect('car_detail', cat_id=category_id)
    else:
        form = IssueCategoryForm(instance=category)
        print(form.errors)
    subcategories = IssueCategory.objects.filter(parent_category=category)
    return render(request, 'issue_category_form.html', {'form': form, 'subcategories': subcategories, 'page_title': page_title})


@user_passes_test(is_admin)
@login_required
def issue_category_delete(request, category_id):
    category = get_object_or_404(IssueCategory, id=category_id)
    if request.method == 'POST':
        category.delete()
        return redirect('manage_issue_categories')
    return render(request, 'issue_category_confirm_delete.html', {'category': category})



@user_passes_test(is_admin)
@login_required
def manage_issues(request):
    page_title = "مدیریت خطاها"
    issues = Issue.objects.all()
    return render(request, 'manage_issues.html', {'issues': issues, 'page_title': page_title})



@user_passes_test(is_admin)
@login_required
def issue_create(request):
    page_title = "ایجاد خطا"
    if request.method == 'POST':
        form = IssueForm(request.POST)
        if form.is_valid():
            issue = form.save()
            return redirect('issue_detail', issue_id=issue.id)
    else:
        form = IssueForm()
    return render(request, 'issue_form.html', {'form': form, 'page_title': page_title})




@login_required
@user_passes_test(is_admin)
def issue_cat_create(request, cat_id):
    page_title = "ایجاد خطا"
    category = get_object_or_404(IssueCategory, id=cat_id)

    if request.method == 'POST':
        form = IssueCatForm(request.POST)
        if form.is_valid():
            issue = form.save(commit=False)  # Create issue instance without saving
            issue.category = category  # Set the category to the selected one
            issue.save()  # Save the issue instance
            form.save_m2m()  # Save many-to-many relationships (tags)
            return redirect('issue_detail', issue_id=issue.id)
    else:
        form = IssueCatForm()

    return render(request, 'issue_cat_form.html', {'form': form, 'page_title': page_title, 'category': category})



@user_passes_test(is_admin)
@login_required
def issue_update(request, issue_id):
    page_title = "ویرایش خطا"
    issue = get_object_or_404(Issue, id=issue_id)
    if request.method == 'POST':
        form = IssueForm(request.POST, instance=issue)
        if form.is_valid():
            form.save()
            return redirect('manage_issues')
    else:
        form = IssueForm(instance=issue)
    return render(request, 'issue_form.html', {'form': form, 'page_title': page_title})


@user_passes_test(is_admin)
@login_required
def issue_delete(request, issue_id):
    issue = get_object_or_404(Issue, id=issue_id)
    if request.method == 'POST':
        issue.delete()
        return redirect('manage_issues')
    return render(request, 'issue_confirm_delete.html', {'issue': issue})



@user_passes_test(is_admin)
@login_required
def manage_solutions(request):
    page_title = "مدیریت راهکارها"
    solutions = Solution.objects.all()
    return render(request, 'manage_solutions.html', {'solutions': solutions, 'page_title': page_title})


@user_passes_test(is_admin)
@login_required
def solution_create(request):
    page_title = "ایجاد راهکار"
    if request.method == 'POST':
        form = SolutionForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('manage_solutions')
    else:
        form = SolutionForm()
    return render(request, 'solution_form.html', {'form': form, 'page_title': page_title})




@user_passes_test(is_admin)
@login_required
def solution_update(request, solution_id):
    page_title = "ویرایش راهکار"
    solution = get_object_or_404(Solution, id=solution_id)
    if request.method == 'POST':
        form = SolutionForm(request.POST, instance=solution)
        if form.is_valid():
            form.save()  
            form.save_m2m()  # ذخیره روابط m2m
            return redirect('manage_solutions')
        else:
            print(form.errors)    



            return redirect('manage_solutions')
    else:

        form = SolutionForm(instance=solution)
    return render(request, 'solution_form.html', {'form': form, 'page_title': page_title, 'solution':solution})






@user_passes_test(is_admin)
@login_required
def solution_delete(request, solution_id):
    solution = get_object_or_404(Solution, id=solution_id)
    if request.method == 'POST':
        solution.delete()
        return redirect('manage_solutions')
    return render(request, 'solution_confirm_delete.html', {'solution': solution})


@user_passes_test(is_admin)
@login_required
def manage_subscriptions(request):
    page_title = "مدیریت اشتراک"
    subscriptions = Subscription.objects.all()
    return render(request, 'manage_subscriptions.html', {'subscriptions': subscriptions, 'page_title': page_title})


@user_passes_test(is_admin)
@login_required
def subscription_create(request):
    page_title = "ایجاد اشتراک"
    if request.method == 'POST':
        form = SubscriptionForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('manage_subscriptions')
    else:
        form = SubscriptionForm()
    return render(request, 'subscription_form.html', {'form': form, 'page_title': page_title})



@user_passes_test(is_admin)
@login_required
def subscription_update(request, subscription_id):
    page_title = "ویرایش اشتراک"
    subscription = get_object_or_404(Subscription, id=subscription_id)
    if request.method == 'POST':
        form = SubscriptionForm(request.POST, instance=subscription)
        if form.is_valid():
            form.save()
            return redirect('manage_subscriptions')
    else:
        form = SubscriptionForm(instance=subscription)
    return render(request, 'subscription_form.html', {'form': form, 'page_title': page_title})




def upgrade_subscription(user, new_access_level):
    subscription = Subscription.objects.get(user=user)
    subscription.access_level = new_access_level
    subscription.save()


    

@user_passes_test(is_admin)
@login_required
def subscription_delete(request, subscription_id):
    subscription = get_object_or_404(Subscription, id=subscription_id)
    if request.method == 'POST':
        subscription.delete()
        return redirect('manage_subscriptions')
    return render(request, 'subscription_confirm_delete.html', {'subscription': subscription})





class CustomLoginView(LoginView):
    def is_admin(self, user):
        return user.role == 'admin' or user.is_superuser

    def get_success_url(self):
        if self.is_admin(self.request.user):
            return reverse('admin_dashboard')
        else:
            return reverse('home')

    def form_valid(self, form):
        # Instead of form.save(), we authenticate the user
        login(self.request, form.get_user())  # Log the user in

        # ثبت زمان ورود
        UserActivity.objects.create(user=form.get_user())  # Log user session
        return super().form_valid(form)






class LogoutView(AuthLogoutView):
    def dispatch(self, request, *args, **kwargs):
        user_activity = UserActivity.objects.filter(user=request.user, logout_time__isnull=True).first()
        if user_activity:
            user_activity.logout_time = timezone.now()
            user_activity.save()
        else:
            # Handle the case when no active session is found
            pass

        return super().dispatch(request, *args, **kwargs)





def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'ثبت نام با موفقیت انجام شد. به صفحه ورود بروید.')
            return redirect(reverse('login'))  # به صفحه ورود ریدایرکت کنید
        else:
            messages.error(request, 'ثبت نام ناموفق. لطفاً خطاها را بررسی کنید.')
    else:
        form = CustomUserCreationForm()
    return render(request, 'register.html', {'form': form})










def search(request):
    form = SearchForm(request.GET or None)
    results = []

    if form.is_valid():
        query = form.cleaned_data.get('query', '')
        filter_options = request.GET.getlist('filter_option', ['all'])  # دریافت لیست فیلترها

        # بررسی دسترسی کاربر
        user = request.user
        subscription = getattr(user, 'subscription', None)

        # اگر کاربر اشتراک نداشته باشد، دسترسی محدود است
        if not subscription:
            return render(request, 'search_results.html', {'form': form, 'results': []})

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
            results.extend([{'car': car} for car in cars])

        if 'issues' in filter_options or 'all' in filter_options:
            results.extend([{'issue': issue, 'full_category_name': issue.category.get_full_category_name()} for issue in issues])

        if 'solutions' in filter_options or 'all' in filter_options:
            for solution in solutions:
                for issue in solution.issues.filter(category__in=allowed_categories):
                    results.append({
                        'solution': solution,
                        'issue': issue,
                        'full_category_name': issue.category.get_full_category_name(),
                    })

        if 'tags' in filter_options or 'all' in filter_options:
            for tag in tags:
                associated_issues = tag.issues.filter(category__in=allowed_categories)
                associated_solutions = tag.solutions.filter(issues__category__in=allowed_categories) if subscription.plan.access_to_diagnostic_steps else []
                for issue in associated_issues:
                    results.append({
                        'tag': tag,
                        'issue': issue,
                        'full_category_name': issue.category.get_full_category_name(),
                    })
                for solution in associated_solutions:
                    for issue in solution.issues.filter(category__in=allowed_categories):
                        results.append({
                            'tag': tag,
                            'solution': solution,
                            'issue': issue,
                            'full_category_name': issue.category.get_full_category_name(),
                        })

        # حذف نتایج تکراری
        unique_results = []
        seen = set()
        for result in results:
            result_tuple = tuple(result.items())
            if result_tuple not in seen:
                seen.add(result_tuple)
                unique_results.append(result)

    return render(request, 'search_results.html', {'form': form, 'results': unique_results})


    










@user_passes_test(is_admin)
@login_required
def cat_detail(request, cat_id):
    page_title = "دسته"
    
    cat = get_object_or_404(IssueCategory, id=cat_id)
    issue_categories = IssueCategory.objects.filter(parent_category=cat_id)  
    return render(request, 'car_detail.html', {'cat': cat, 'issue_categories': issue_categories, 'page_title': page_title})


@login_required
def user_cat_detail(request, cat_id):
    page_title = "دسته"
    issue_categoriess = IssueCategory.objects.all()
    cat = get_object_or_404(IssueCategory, id=cat_id)
    issue_categories = IssueCategory.objects.filter(parent_category=cat_id)  
    return render(request, 'user_car_detail.html', {'issue_categoriess':issue_categoriess, 'cat': cat, 'issue_categories': issue_categories, 'page_title': page_title})



@user_passes_test(is_admin)
def issue_detail(request, issue_id):
    issue = get_object_or_404(Issue, id=issue_id)
    question = issue.question  # سوال مرتبط با خطا (در صورت وجود)
    solutions = Solution.get_filtered_solutions(issue_id = issue.id)
    form = issue_SolutionForm()

    issue_form = IssueCatForm(instance=issue)

    if question:
        options = question.options.all()
        return render(request, 'issue_detail.html', {'issue_form':issue_form,'form':form,'issue': issue, 'question': question, 'options': options, 'solutions':solutions})
    else:
        steps = issue.diagnostic_steps.all()  # مراحل عیب‌یابی مستقیم
        return render(request, 'issue_detail.html', {'issue_form':issue_form,'form':form,'issue': issue, 'steps': steps,'solutions':solutions})



@user_passes_test(is_admin)
def step_detail(request, step_id):
    step = get_object_or_404(DiagnosticStep, id=step_id)
    issue_categories = IssueCategory.objects.all()
    question = step.question # سوال مرتبط با خطا (در صورت وجود)
    
    solution = step.solution
    if solution:
        form = issue_SolutionForm(instance=solution)
    else:
        form = issue_SolutionForm()
    if question:
        options = question.options.all()
        return render(request, 'step_detail.html', {'form':form,'issue_categories':issue_categories,'step': step, 'question': question, 'options': options})
    else:
        
        return render(request, 'step_detail.html', {'form':form,'issue_categories':issue_categories, 'step': step})



@login_required
@has_diagnostic_access
def user_step_detail(request, step_id):
    step = get_object_or_404(DiagnosticStep, id=step_id)
    
    question = step.question # سوال مرتبط با خطا (در صورت وجود)
    if question:
        options = Option.objects.filter(question_id=question.id)
        return render(request, 'user_step_detail.html', {'step': step, 'question': question, 'options': options})
    else:
        return render(request, 'user_step_detail.html', {'step': step})


@user_passes_test(is_admin)
@login_required
def solution_detail(request, solution_id):
    page_title = " راهکار"
    solution = get_object_or_404(Solution, id=solution_id)
    return render(request, 'solution_detail.html', {'solution': solution, 'page_title': page_title})



@user_passes_test(is_admin)
@login_required
def manage_cars(request):
    page_title = "مدیریت خودرو ها"
    cars = IssueCategory.objects.filter(parent_category__isnull=True)
    return render(request, 'manage_cars.html', {'cars': cars, 'page_title': page_title})



@user_passes_test(is_admin)
@login_required
def car_detail(request, cat_id):
    page_title = " خودرو"
    car = get_object_or_404(IssueCategory, id=cat_id)
    issue_categories = IssueCategory.objects.filter(parent_category=cat_id)
    issue_categoriess = IssueCategory.objects.all()
    issues = Issue.objects.filter(category=cat_id)
    maps = Map.objects.filter(category=cat_id)
    articles = Article.objects.filter(category=cat_id)
    return render(request, 'car_detail.html', {'articles':articles,'car':car, 'issue_categoriess': issue_categoriess,'issue_categories': issue_categories, 'issues':issues, 'maps':maps, 'page_title': page_title})



@login_required
@has_category_access
def user_car_detail(request, cat_id):
    page_title = " خودرو"
    car = get_object_or_404(IssueCategory, id=cat_id)
    issue_categories = IssueCategory.objects.filter(parent_category=cat_id)
    issue_categoriess = IssueCategory.objects.all()
    issues = Issue.objects.filter(category=cat_id)
    return render(request, 'user_car_detail.html', {'issue_categoriess':issue_categoriess, 'car':car, 'issue_categories': issue_categories, 'issues':issues, 'page_title': page_title})





@login_required
def user_solution_detail(request, solution_id):
    page_title = " راهکار"

    issue_categoriess = IssueCategory.objects.all()
    solution = get_object_or_404(Solution, id=solution_id)
    return render(request, 'user_solution_detail.html', {'issue_categoriess':issue_categoriess, 'solution': solution, 'page_title': page_title})




@login_required
def user_issue_detail(request, issue_id):
    page_title = " خطا"
    issue = get_object_or_404(Issue, id=issue_id)
    page_title = issue.title
    question = issue.question
    
    issue_categoriess = IssueCategory.objects.all()
    if question:
        options = question.options.all()
        return render(request, 'user_issue_detail.html', {'issue_categoriess':issue_categoriess, 'issue': issue, 'question': question, 'options': options})
    else:
        return render(request, 'user_issue_detail.html', {'issue_categoriess':issue_categoriess,'issue': issue})




@login_required
def user_article_detail(request, article_id):
    article = get_object_or_404(Article, id=article_id)
    print(article.content)
    question = article.question
    
    issue_categoriess = IssueCategory.objects.all()
    if question:
        options = question.options.all()
        return render(request, 'user_article_detail.html', {'issue_categoriess':issue_categoriess, 'article': article, 'question': question, 'options': options})
    else:
        return render(request, 'user_article_detail.html', {'issue_categoriess':issue_categoriess,'article': article})






@login_required
def bookmark_create(request):
    if request.method == 'POST':
        url = request.POST.get('url')
        title = request.POST.get('title')
        try:
            Bookmark.objects.get_or_create(user=request.user, url=url, title=title)
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})



@login_required
def manage_bookmarks(request):
    page_title = "مدیریت نشان ها"
    bookmarks = Bookmark.objects.filter(user=request.user)
    return render(request, 'manage_bookmarks.html', {'bookmarks': bookmarks, 'page_title': page_title})


@login_required
def bookmark_delete(request, bookmark_id):
    bookmark = get_object_or_404(Bookmark, id=bookmark_id, user=request.user)
    bookmark.delete()
    return redirect('manage_bookmarks')


@user_passes_test(is_admin)
@login_required
def create_diagnostic_steps(request, issue_id):
    issue = get_object_or_404(Issue, id=issue_id)
    # question = issue.question  # فرض بر این است که یک سوال به هر مشکل مربوط است
    question = issue.question
    print(question)
    if request.method == 'POST':
        form = DiagnosticStepForm(request.POST, question=question)
        if form.is_valid():
            diagnostic_step = form.save(commit=False)
            diagnostic_step.issue = issue  # اطلاعات مربوط به مشکل را تنظیم کنید
            diagnostic_step.save()
            return redirect('create_diagnostic_steps', issue_id=issue_id)
    else:
        form = DiagnosticStepForm(question=question)

    return render(request, 'create_diagnostic_steps.html', {'form': form})



@user_passes_test(is_admin)
@login_required
def diagnostic_process_view(request, issue_id):
    issue = Issue.objects.get(id=issue_id)
    steps = DiagnosticStep.objects.filter(issue=issue).order_by('order')

    return render(request, 'diagnostic_process.html', {'issue': issue, 'steps': steps})



@login_required
def option_diagnostic_steps(request, issue_id, option_id, order):
    issue_categoriess = IssueCategory.objects.all()
    issue = Issue.objects.get(id=issue_id)
    if option_id == 'None':
        step = get_object_or_404(DiagnosticStep, issue=issue, order=order)
        return render(request, 'diagnostic_steps.html', {'step': step, 'issue_categoriess':issue_categoriess, 'issue_id':issue_id, 'option_id':'None','order':order+1, 'issue':issue})
    else:
        option_id = int(option_id)
        print(option_id)
        step = get_object_or_404(DiagnosticStep, issue=issue, option=option_id, order=order)
        return render(request, 'diagnostic_steps.html', {'step': step, 'issue_categoriess':issue_categoriess, 'issue_id':issue_id, 'option_id':option_id, 'order':order+1, 'issue':issue})
        

@user_passes_test(is_admin)
@login_required
def add_question(request):
    if request.method == "POST":
        form = QuestionForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('question_list')  # می‌توانید به یک صفحه دیگر یا لیست سوالات تغییر دهید
    else:
        form = QuestionForm()
    return render(request, 'question_form.html', {'form': form})





@user_passes_test(is_admin)
@login_required
def create_option(request, question_id):
    question = get_object_or_404(Question, id=question_id)
    if request.method == "POST":
        form = OptionForm(request.POST)
        if form.is_valid():
            option = form.save(commit=False)
            option.question = question
            option.save()
            return redirect('issue_detail', issue_id=question.issue.id)
    else:
        form = OptionForm()
    return render(request, 'option_form.html', {'form': form, 'question':question})



@user_passes_test(is_admin)
@login_required
def issue_solution_create(request, issue_id):
    page_title = "ایجاد راهکار برای خطا"
    if request.method == 'POST':
        form = SolutionForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('manage_solutions')
    else:
        form = SolutionForm()
    return render(request, 'solution_form.html', {'form': form, 'page_title': page_title})



@login_required
@csrf_exempt
def get_solutions(request, issue_id):

    solutions = []
    
    for solution in Solution.get_filtered_solutions(issue_id = issue_id):
        hierarchy = solution.get_issue_hierarchy()  # دریافت هرم مسائل
        solutions.append({
            'id': solution.id,
            'title': solution.title,
            'hierarchy': hierarchy  # اضافه کردن هرم مسائل به پاسخ
        })
    print(solutions)
    return JsonResponse({'solutions': solutions})




@csrf_exempt  
def get_selected_solutions(request, issue_id):

    try:
        issue = get_object_or_404(Issue, id=issue_id)
        question = issue.question
        # دریافت سوالات مرتبط با خطا


        selected_data = []


        if question:
            options = Option.objects.filter(question_id=question.id)
            for option in options:
                solutions = list(
                DiagnosticStep.objects.filter(option_id=option.id, issue_id=issue_id)  # فیلتر کردن بر اساس گزینه و مسئله
                .values('id', 'order', solution_title=models.F('solution__title'))
                .order_by('order')
                )

                selected_data.append({
                    'id': option.id,
                    'text': option.text,
                    'solutions': solutions  # Add the solutions specific to the option
                })
        else:


            solutions = list(
                DiagnosticStep.objects.filter(issue_id=issue_id)  # فیلتر کردن بر اساس گزینه و مسئله
                .values('id', 'order', solution_title=models.F('solution__title'))
                .order_by('order')
                )

            selected_data.append({
                'solutions': solutions  # Add the solutions specific to the option
            })
        print(selected_data)
        return JsonResponse({'selected': selected_data})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)




@csrf_exempt
@user_passes_test(is_admin)
@login_required
def update_selection(request):
    if request.method == 'POST':
        solution_id = request.POST.get('id')
        option_id = request.POST.get('option_id', 'none')
        issue_id = request.POST.get('issue_id')

        # Validate issue_id
        if not issue_id or not issue_id.isdigit():
            return JsonResponse({'status': 'fail', 'error': 'Invalid issue ID'}, status=400)
        
        issue_id = int(issue_id)
        
        # Validate option_id
        if option_id != 'none':
            if not option_id or not option_id.isdigit():  # Check if it's a valid number
                return JsonResponse({'status': 'fail', 'error': 'Invalid option ID'}, status=400)
            option_id = int(option_id)

        # Now you can safely filter and proceed
        current_steps_count = DiagnosticStep.objects.filter(issue_id=issue_id, option_id=option_id if option_id != 'none' else None).count()
        new_order = current_steps_count + 1
        
        new_step = DiagnosticStep(
            solution_id=solution_id,
            issue_id=issue_id,
            order=new_order,
        )

        if option_id != 'none':
            new_step.option_id = option_id

        new_step.save()
        return JsonResponse({'status': 'success', 'message': 'Selection saved successfully.'})
    
    return JsonResponse({'status': 'fail'}, status=400)




@user_passes_test(is_admin)
@login_required
@csrf_exempt
def delete_selection(request):
    if request.method == 'POST':
        id = request.POST.get('id')
        issue_id = request.POST.get('issue_id')

        try:
            step = DiagnosticStep.objects.get(id=id, issue_id=issue_id)
            step.delete()
            return JsonResponse({'status': 'success'})
        except DiagnosticStep.DoesNotExist:
            return JsonResponse({'status': 'fail', 'error': 'Selection not found'}, status=404)

    return JsonResponse({'status': 'fail'}, status=400)



@csrf_exempt
def get_options(request, question_id):
    options = Option.objects.filter(question_id=question_id)
    options_data = []
    
    question = get_object_or_404(Question, id=question_id)
    
    for option in options:
        next_step = option.next_step
        
        # Prepare next_step data
        if next_step:
            next_step_data = {
                'id': next_step.id,
            }
        else:
            next_step_data = None  # or any default value that makes sense

        options_data.append({
            'id': option.id,
            'text': option.text,
            'next_step': next_step_data,  # Now `next_step` is a dictionary
            'option_url': f"/step/{option.next_step.id}" if option.next_step else f"/articles/{option.article.id}" if option.article else f"/issue/{option.issue.id}" if option.issue else None, # افزودن option_url
            'user_option_url': f"/user_step/{option.next_step.id}" if option.next_step else f"/user_issue/{option.issue.id}" if option.issue else f"/user_articles/{option.article.id}" if option.article else None
        })
        print(options_data)
    
    return JsonResponse({'options': options_data})





@csrf_exempt
def get_step_options(request, step_id):
    try:
        step = DiagnosticStep.objects.get(id=step_id)
        # Get the related Question
        question = step.question
        if question is None:
            return JsonResponse({'options': []}, status=200)  # or appropriate response for no question
        
        options = Option.objects.filter(question_id=question.id)
        # Convert QuerySet to a list of dictionaries
        options_list = []
        for option in options:
            option_dict = {
                'id': option.id,
                'text': option.text,
                'next_step': option.next_step.id if option.next_step else None,  # اگر next_step وجود نداشت مقدار None بده
                'option_url': f"/step/{option.next_step.id}" if option.next_step else f"/issue/{option.issue.id}" if option.issue else f"/articles/{option.article.id}" if option.article else None, # افزودن option_url
                'user_option_url': f"/user_step/{option.next_step.id}" if option.next_step else f"/user_issue/{option.issue.id}" if option.issue else f"/user_articles/{option.article.id}" if option.article else None
            }
            options_list.append(option_dict)

        return JsonResponse({'status': 'success', 'options': options_list}, status=200)
    
    except DiagnosticStep.DoesNotExist:
        return JsonResponse({'error': 'Diagnostic step not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)




# @user_passes_test(is_admin)
# def user_list(request):
#     users = CustomUser.objects.all()
#     return render(request, 'user_list.html', {'users': users})


@user_passes_test(is_admin)
def user_create(request):
    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('manage_users')
    else:
        form = UserForm()
    return render(request, 'user_form.html', {'form': form})

@user_passes_test(is_admin)
def user_update(request, pk):
    user = get_object_or_404(CustomUser, pk=pk)
    if request.method == 'POST':
        form = UserForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('manage_users')
    else:
        form = UserForm(instance=user)
    return render(request, 'user_form.html', {'form': form})




@user_passes_test(is_admin)
def user_delete(request, pk):
    user = get_object_or_404(CustomUser, pk=pk)
    if request.method == 'POST':
        user.delete()
        return redirect('manage_users')
    return render(request, 'user_confirm_delete.html', {'user': user})



@user_passes_test(is_admin)
@login_required
@csrf_exempt
def create_question(request):
    if request.method == 'POST':
        text = request.POST.get('text')
        issue_id = request.POST.get('issue_id')
        article_id = request.POST.get('article_id')
        if issue_id:
            try:
                question = Question.objects.create(text=text)
                Issue.objects.filter(id=issue_id).update(question=question.id)

                return JsonResponse({'status': 'success'})
            except Exception as e:
                return JsonResponse({'status': 'error', 'message': str(e)})
        elif article_id:
            try:
                question = Question.objects.create(text=text)
                Article.objects.filter(id=article_id).update(question=question.id)

                return JsonResponse({'status': 'success'})
            except Exception as e:
                return JsonResponse({'status': 'error', 'message': str(e)})




@user_passes_test(is_admin)
@login_required
@csrf_exempt
def create_step_question(request):
    if request.method == 'POST':
        text = request.POST.get('text')
        step_id = request.POST.get('step_id')
        try:
            # Create a new question
            question = Question.objects.create(text=text)
            created = True
            # Get the DiagnosticStep instance
            step = DiagnosticStep.objects.get(id=step_id)

            # Set the question for this step
            step.question = question
            step.save()

            return JsonResponse({'status': 'success', 'created': created})
        except DiagnosticStep.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Step not found'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})


@user_passes_test(is_admin)
@login_required
@csrf_exempt
def issue_option(request):
    if request.method == 'POST':
        text = request.POST.get('text')
        issue_id = request.POST.get('issue_id')
        question_id = request.POST.get('question_id')
        step_id = request.POST.get('step_id')  # شناسه مرحله
        solution_id = request.POST.get('solution_id')  # شناسه راهکار
        nextissue_id = request.POST.get('nextissueId')
        issue = get_object_or_404(Issue, id=issue_id)
        question = get_object_or_404(Question, id=question_id)
        
        # اگر شناسه مرحله موجود بود
        if step_id:
            step = get_object_or_404(DiagnosticStep, id=step_id)
            option = Option.objects.create(text=text, question=question, next_step=step)
            return JsonResponse({'status': 'success'})

        if nextissue_id:
            issue = get_object_or_404(Issue, id=nextissue_id)
            print(issue)
            option = Option.objects.create(text=text, question=question, issue=issue)
            return JsonResponse({'status': 'success'})
        # اگر شناسه راهکار موجود بود
        elif solution_id:
            solution = get_object_or_404(Solution, id=solution_id)

            step = DiagnosticStep.objects.create(issue=issue, solution=solution)
            option = Option.objects.create(text=text, question=question, next_step=step)
            return JsonResponse({'status': 'success'})
        else:
            step = DiagnosticStep.objects.create(issue=issue)
            option = Option.objects.create(text=text, question=question, next_step=step)
            return JsonResponse({'status': 'success'})

        return JsonResponse({'status': 'error', 'message': 'کدام شناسه ارسال نشده است.'})




@user_passes_test(is_admin)
@login_required
@csrf_exempt
def add_option(request):
    if request.method == 'POST':
        text = request.POST.get('text')
        issue_id = request.POST.get('issue_id')
        article_id = request.POST.get('article_id')
        question_id = request.POST.get('question_id')
        step_id = request.POST.get('step_id')  # شناسه مرحله
        solution_id = request.POST.get('solution_id')  # شناسه راهکار
        nextissue_id = request.POST.get('nextissueId')
        nextarticle_id = request.POST.get('nextarticleId')
        
        question = get_object_or_404(Question, id=question_id)
        print(f"article id is: ",nextarticle_id)
        # اگر شناسه مرحله موجود بود
        if step_id:
            step = get_object_or_404(DiagnosticStep, id=step_id)
            option = Option.objects.create(text=text, question=question, next_step=step)
            return JsonResponse({'status': 'success'})
        
        if article_id:
            article = get_object_or_404(Article, id=article_id)
            print(article)

            option = Option.objects.create(text=text, question=question, article=article)
            return JsonResponse({'status': 'success'})
        if nextissue_id:
            issue = get_object_or_404(Issue, id=nextissue_id)
            option = Option.objects.create(text=text, question=question, issue=issue)
            return JsonResponse({'status': 'success'})
        # اگر شناسه راهکار موجود بود
        elif solution_id:
            solution = get_object_or_404(Solution, id=solution_id)

            step = DiagnosticStep.objects.create(issue=issue, solution=solution)
            option = Option.objects.create(text=text, question=question, next_step=step)
            return JsonResponse({'status': 'success'})
        
        else:
            if issue_id:
                issue = get_object_or_404(Issue, id=issue_id)
                step = DiagnosticStep.objects.create(issue=issue)
            
            option = Option.objects.create(text=text, question=question, next_step=step)
            return JsonResponse({'status': 'success'})

        return JsonResponse({'status': 'error', 'message': 'کدام شناسه ارسال نشده است.'})






@user_passes_test(is_admin)
@login_required
@csrf_exempt
def create_solution(request):
    if request.method == 'POST':
        form = issue_SolutionForm(request.POST)
        
        if form.is_valid():
            solution = form.save(commit=False)
            solution.save()
            form.save()  
            form.save_m2m()    
            issue_id = request.POST.get("issue_id")
            step_id = request.POST.get('step_id')
            step = get_object_or_404(DiagnosticStep, id=step_id)
            if issue_id:
                issue = Issue.objects.get(id=issue_id)
                solution.issues.add(issue)
            if step_id:
                step.solution = solution
                step.save()
            return JsonResponse({
                'status': 'success',
                'solution': {
                    'id': solution.id,
                    'title': solution.title,
                }
            })

        return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)




@login_required
def diagnostic_process(request, issue_id):
    issue = get_object_or_404(Issue, id=issue_id)
    first_question = issue.question
    
    context = {
        'issue': issue,
        'question': first_question
    }
    
    return render(request, 'diagnostic_process.html', context)



@login_required
def load_next_step(request, option_id):
    # Initialize defaults
    question = None
    options = []
    solution = None

    option = get_object_or_404(Option, id=option_id)
    
    if option.next_step:
        question = option.next_step.question
        solution = option.next_step.solution

        # Check if there is a question associated with the next step
        if question:
            options = [{'id': opt.id, 'text': opt.text, 'next_step': opt.next_step.id} for opt in question.options.all()]
        
        # Prepare solution data for JSON serialization
        if solution:
            solution_data = {
                'title': solution.title,        # Example of including id
                'description': solution.description,    # Include any relevant fields here
                # Add more fields as necessary
            }


        # Responding with options including the respective URL
        response_data = {
            'status': 'success',
            'options': [
                {
                    'text': opt['text'],
                    'url': f"/step/{opt['next_step']}/"  # Creating the link in the backend
                } for opt in options
            ],
            'solution': solution_data
        }

        return JsonResponse(response_data)

    return JsonResponse({'status': 'error', 'message': 'No next step available.'}, status=404)



# @csrf_exempt
# def add_tag(request):
#     if request.method == 'POST':
#         tag_name = request.POST.get('name')
#         tag, created = Tag.objects.get_or_create(name=tag_name)
#         return JsonResponse({'status': 'success', 'tag': {'id': tag.id, 'name': tag.name}} if created else {'status': 'exists'})
#     return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)


@user_passes_test(is_admin)
@login_required
@csrf_exempt
def update_option(request, option_id):
    if request.method == 'POST':
        text = request.POST.get('text')
        try:
            option = get_object_or_404(Option, id=option_id)
            option.text = text
            option.save()
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})





@user_passes_test(is_admin)
@login_required
@csrf_exempt
def delete_option(request, option_id):
    if request.method == 'DELETE':  # Handle DELETE request
        try:
            option = get_object_or_404(Option, id=option_id)
            option.delete()
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)  # For unsupported methods



@user_passes_test(is_admin)
@login_required
@csrf_exempt
def update_question(request, question_id):
    if request.method == 'POST':
        text = request.POST.get('text')
        try:
            question = get_object_or_404(Question, id=question_id)
            question.text = text
            question.save()
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})



@user_passes_test(is_admin)
@login_required
@csrf_exempt
def delete_question(request, question_id):
    question = get_object_or_404(Question, id=question_id)
    question.delete()
    return JsonResponse({'status': 'success'})




@login_required
@csrf_exempt
def get_steps(request, issue_id):
    steps = list(DiagnosticStep.objects.filter(issue_id=issue_id).values('id', 'letter'))  # عناوین مراحل
    return JsonResponse({'steps': steps})



# @csrf_exempt
# def get_tags(request):
#     tags = Tag.objects.values('id', 'name')
#     return JsonResponse(list(tags), safe=False)









@user_passes_test(is_admin)
@login_required
@csrf_exempt
def add_tag(request):
    tag_name = request.POST.get('tag_name')
    

    if tag_name:
        tag, created = Tag.objects.get_or_create(name=tag_name)
        return JsonResponse({'success': True, 'tag_id': tag.id, 'tag_name': tag.name})

    return JsonResponse({'success': False})





class CategorizationView(View):
    def post(self, request):
        category_name = request.POST.get('category_name')

        # تجزیه ی نام دسته بندی به قسمت های مربوطه
        names = category_name.split('::')
        parent = None

        for name in names:
            # جستجو برای دسته بندی والد
            parent_category, created = IssueCategory.objects.get_or_create(
                name=name,
                parent_category=parent
            )
            parent = parent_category  # به روزرسانی والد برای دسته بندی زیرین

        return JsonResponse({'message': 'دسته بندی ایجاد شد', 'category_id': parent.id}, status=201)



class MapCategorizationView(View):
    def post(self, request):
        category_name = request.POST.get('category_name')

        # تجزیه ی نام دسته بندی به قسمت های مربوطه
        names = category_name.split('::')
        parent = None

        for name in names:
            # جستجو برای دسته بندی والد
            parent_category, created = MapCategory.objects.get_or_create(
                name=name,
                parent_category=parent
            )
            parent = parent_category  # به روزرسانی والد برای دسته بندی زیرین

        return JsonResponse({'message': 'دسته بندی ایجاد شد', 'category_id': parent.id}, status=201)




@csrf_exempt  # فقط در حالت توسعه از csrf_exempt استفاده کنید

@user_passes_test(is_admin)
@login_required
def import_issues(request, car_id):
    if request.method == 'POST' and request.FILES.get('file'):
        excel_file = request.FILES['file']
        try:
            # بارگذاری داده‌های Excel
            df = pd.read_excel(excel_file)

            # بررسی وجود ستون‌های الزامی
            required_columns = ['title', 'description']
            category = IssueCategory.objects.get(id=car_id)
            for col in required_columns:
                if col not in df.columns:
                    return JsonResponse({'status': 'error', 'message': f'Missing column: {col}'})

            # پردازش هر ردیف در DataFrame
            for index, row in df.iterrows():
                title = row['title']
                description = row['description']

                # اعتبارسنجی عنوان و دسته‌بندی
                if not title:
                    continue  # اگر عنوان خالی باشد، آن را نادیده بگیرید

                # ایجاد شیء Issue
                Issue.objects.create(title=title, description=description, category=category)

            return JsonResponse({'status': 'success', 'message': 'Issues imported successfully.'})

        except IssueCategory.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': f'Category ID {car_id} does not exist.'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'error', 'message': 'No file uploaded.'})




@user_passes_test(is_admin)
@login_required
@csrf_exempt  # Consider CSRF tokens for security in production
def import_maps(request, category_id):
    if request.method == 'POST':
        image_files = request.FILES.getlist('image_files')  # Get list of uploaded images
        txt_files = request.FILES.getlist('txt_files')      # Get list of associated TXT files

        if len(image_files) != len(txt_files):
            return JsonResponse({'status': 'error', 'message': 'Each image must have a corresponding TXT file.'})

        try:
            # Check if the category exists
            category = IssueCategory.objects.get(id=category_id)
            responses = []

            for idx, txt_file in enumerate(txt_files):
                image_file = image_files[idx]

                # Process the TXT file to extract a single tag
                try:
                    raw_content = txt_file.read().decode('utf-8-sig')  # Decode and handle BOM
                    cleaned_content = raw_content.replace('\u201c', '').replace('\u201d', '').strip()
                except UnicodeDecodeError:
                    return JsonResponse({'status': 'error', 'message': f'Error decoding file: {txt_file.name}'})

                if cleaned_content:
                    # Create or get a single Tag instance for the entire file content
                    tag, created = Tag.objects.get_or_create(name=cleaned_content)

                    # Extract title without file extension
                    file_name, _ = os.path.splitext(image_file.name)

                    # Create the Map object
                    map_instance = Map.objects.create(title=file_name, image=image_file, category=category)
                    map_instance.tags.add(tag)  # Associate the tag with the map

                    responses.append({
                        'title': map_instance.title,
                        'status': 'success',
                        'message': f'Map uploaded successfully with tag: {tag.name}.'
                    })
                else:
                    responses.append({
                        'title': image_file.name,
                        'status': 'error',
                        'message': f'TXT file {txt_file.name} is empty or invalid.'
                    })

            return JsonResponse({'status': 'success', 'message': responses})

        except IssueCategory.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': f'Category ID {category_id} does not exist.'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'})




@user_passes_test(is_admin)
@login_required
@api_view(['POST'])
def add_map(request):
    serializer = MapSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({'status': 'success'}, status=status.HTTP_201_CREATED)
    return Response({'status': 'error', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)




@login_required
@api_view(['GET'])
def get_maps(request):
    maps = Map.objects.all()
    serializer = MapSerializer(maps, many=True)
    return Response({'maps': serializer.data})




@user_passes_test(is_admin)
@login_required
@csrf_exempt
def set_solution(request):
    if request.method == 'POST':
        solution_id = request.POST.get('solution_id')
        step_id = request.POST.get('step_id')
        step = get_object_or_404(DiagnosticStep, id=step_id)
        solution = get_object_or_404(Solution, id=solution_id)
        step.solution = solution
        step.save()
        return JsonResponse({'status': 'success', 'message': 'solution set successfully.'})




@user_passes_test(is_admin)
@login_required
@csrf_exempt
def set_map(request):
    if request.method == 'POST':
        
        map_id = request.POST.get('map_id')
        step_id = request.POST.get('step_id')
        print(map_id)
        step = get_object_or_404(DiagnosticStep, id=step_id)
        map = get_object_or_404(Map, id=map_id)
        
        step.map = map
        step.save()

        return JsonResponse({'status': 'success', 'message': 'map set successfully.'})





@user_passes_test(is_admin)
@login_required
@csrf_exempt
def edit_solution(request):
    if request.method == 'POST':
        solution_id = request.POST.get('id')
        title = request.POST.get('title')
        description = request.POST.get('description')
        try:
            solution = Solution.objects.get(id=solution_id)
            solution.title = title
            solution.description = description
            solution.save()

            return JsonResponse({'status': 'success', 'message': 'ویرایش با موفقیت انجام شد.'})
        except Solution.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'راهکار پیدا نشد.'})

    return JsonResponse({'status': 'error', 'message': 'درخواست نامعتبر است.'})



@user_passes_test(is_admin)
@login_required
def edit_issue(request):
    if request.method == 'POST':
        issue_id = request.POST.get('id')
        title = request.POST.get('title')
        description = request.POST.get('description')
        
        if not title:
            return JsonResponse({'status': 'error', 'message': 'Title is required.'})
        if not issue_id:
            return JsonResponse({'status': 'error', 'message': 'Issue ID is required.'})

        try:
            issue = Issue.objects.get(id=issue_id)
            issue.title = title
            issue.description = description
            issue.save()
            return JsonResponse({'status': 'success', 'message': 'ویرایش با موفقیت انجام شد.'})
        except Issue.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Issue not found.'})




@user_passes_test(is_admin)
@login_required
def map_detail(request, map_id):
    page_title = " نقشه"
    map = get_object_or_404(Map, id=map_id)
    return render(request, 'map_detail.html', {'map': map, 'page_title': page_title})




@login_required
def user_map_detail(request, map_id):
    page_title = " نقشه"
    map = get_object_or_404(Map, id=map_id)
    return render(request, 'user_map_detail.html', {'map': map, 'page_title': page_title})




@user_passes_test(is_admin)
@login_required
def map_cat_create(request, cat_id):
    page_title = "ایجاد نقشه"
    category = get_object_or_404(IssueCategory, id=cat_id)
   
    if request.method == 'POST':
        form = MapForm(request.POST, request.FILES)  # اضافه کردن request.FILES
        if form.is_valid():
            map = form.save(commit=False)
            map.category = category
            map.save()
            form.save_m2m()
            return redirect('map_detail', map_id=map.id)
        else:
            print(form.errors) # برای دیباگ
    else:
        form = MapForm()

    return render(request, 'map_cat_form.html', {'form': form, 'page_title': page_title, 'category': category})



@user_passes_test(is_admin)
@login_required
def manage_maps(request):
    cats = MapCategory.objects.filter(parent_category__isnull=True)
    rendered_categories = render_mapcategories(cats)
    page_title = "مدیریت نقشه ها"
    return render(request, 'manage_maps.html', {'rendered_categories': rendered_categories, 'cats': cats, 'page_title': page_title})


@user_passes_test(is_admin)
@login_required
def mapcat_detail(request, cat_id):
    page_title = " دسته"
    cat = get_object_or_404(MapCategory, id=cat_id)
    maps = Map.objects.filter(category=cat_id)
    map_categories = MapCategory.objects.filter(parent_category=cat_id)

    return render(request, 'mapcat_detail.html', {'map_categories':map_categories, 'maps':maps, 'cat': cat, 'page_title': page_title})






@user_passes_test(is_admin)
@login_required
def map_category_update(request, category_id):
    category = get_object_or_404(MapCategory, id=category_id)
    page_title = "ویرایش دسته"
    if request.method == 'POST':
        form = MapCategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            return redirect('manage_maps')
    else:
        form = MapCategoryForm(instance=category)
    subcategories = MapCategory.objects.filter(parent_category=category)
    return render(request, 'map_cat_form.html', {'form': form, 'subcategories': subcategories, 'page_title': page_title})




@user_passes_test(is_admin)
@login_required
def map_category_delete(request, category_id):
    category = get_object_or_404(MapCategory, id=category_id)
    if request.method == 'POST':
        category.delete()
        return redirect('manage_maps')
    return render(request, 'map_category_confirm_delete.html', {'category': category})






@user_passes_test(is_admin)
@login_required
def map_update(request, map_id):
    page_title = "ویرایش نقشه"
    map = get_object_or_404(Map, id=map_id)
    if request.method == 'POST':
        form = MapForm(request.POST, instance=map)
        if form.is_valid():
            form.save()
            return redirect('manage_maps')
    else:
        form = MapForm(instance=map)
    return render(request, 'map_cat_form.html', {'form': form, 'page_title': page_title})


@user_passes_test(is_admin)
@login_required
def map_delete(request, map_id):
    issue = get_object_or_404(Map, id=map_id)
    if request.method == 'POST':
        issue.delete()
        return redirect('manage_maps')
    return render(request, 'map_confirm_delete.html', {'map': map})



def search_maps(request):
    query = request.GET.get('q', '')
    maps = Map.objects.filter(tags__name__icontains=query)  # Search by tag name
    return render(request, 'map_results.html', {'maps': maps})




def check_bookmark(request):
    if request.method == 'GET':
        url = request.GET.get('url')
        user_bookmarks = Bookmark.objects.filter(user=request.user, url=url)

        return JsonResponse({'exists': user_bookmarks.exists()})




@csrf_exempt
def bulk_delete(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            item_type = data.get('item_type')
            item_ids = data.get('item_ids', [])
            
            # انتخاب مدل مناسب بر اساس نوع آیتم
            if item_type == 'issues':
                model = Issue
            elif item_type == 'articles':
                model = Article
            elif item_type == 'maps':
                model = Map
            else:
                return JsonResponse({'status': 'error', 'message': 'نوع آیتم نامعتبر است'})

            model.objects.filter(id__in=item_ids).delete()
            return JsonResponse({'status': 'success', 'message': 'حذف گروهی با موفقیت انجام شد'})
        
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'درخواست نامعتبر'})

@csrf_exempt
def bulk_update_category(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            item_type = data.get('item_type')
            item_ids = data.get('item_ids', [])
            new_category_id = data.get('new_category_id')
            
            new_category = IssueCategory.objects.get(id=new_category_id)
            
            # انتخاب مدل مناسب بر اساس نوع آیتم
            if item_type == 'issues':
                model = Issue
            elif item_type == 'articles':
                model = Article
            elif item_type == 'maps':
                model = Map
            else:
                return JsonResponse({'status': 'error', 'message': 'نوع آیتم نامعتبر است'})

            model.objects.filter(id__in=item_ids).update(category=new_category)
            return JsonResponse({'status': 'success', 'message': 'بروزرسانی دسته‌بندی با موفقیت انجام شد'})
        
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'درخواست نامعتبر'})

    




def user_detail(request, user_id):
    page_title = "صفحه کاربر"
    user = get_object_or_404(CustomUser, id=user_id)
    user_activities = UserActivity.objects.filter(user_id=user_id).order_by('-login_time')
    
    # Transform dates to Jalali
    for activity in user_activities:
        if activity.login_time:
            # Convert the datetime to Jalali date
            activity.login_time_shamsi = jdatetime.datetime.fromgregorian(datetime=activity.login_time).to_jalali()
        if activity.logout_time:
            activity.logout_time_shamsi = jdatetime.datetime.fromgregorian(datetime=activity.logout_time).to_jalali()

    return render(request, 'user_detail.html', {'user_activities': user_activities, 'user': user})




@login_required
def subscription_plans(request):
    plans = SubscriptionPlan.objects.all()
    return render(request, 'plans.html', {'plans': plans})









@login_required
def subscribe(request, plan_id):
    try:
        # پیدا کردن پلن انتخابی
        plan = get_object_or_404(SubscriptionPlan, id=plan_id)

        # اگر قیمت پلن صفر باشد (رایگان)
        if plan.price == 0:
            # اشتراک را به طور مستقیم فعال می‌کنیم
            user_subscription, created = UserSubscription.objects.get_or_create(
                user=request.user,
                defaults={'plan': plan}
            )

            # تنظیم تاریخ‌ها
            if created:
                user_subscription.start_date = now()
            else:
                if user_subscription.start_date is None:
                    user_subscription.start_date = now()

            user_subscription.end_date = user_subscription.start_date + timedelta(days=30)  # به عنوان مثال 30 روز
            user_subscription.save()

            messages.success(request, 'اشتراک رایگان شما با موفقیت فعال شد.')
            return redirect('my_subscription')  # یا هر صفحه‌ای که می‌خواهید هدایت کنید

        # اگر قیمت پلن غیر از صفر باشد، درخواست پرداخت زرین‌پال را ارسال می‌کنیم
        merchant_id = settings.ZARINPAL_MERCHANT_ID  # تنظیم Merchant ID از تنظیمات
        amount = float(plan.price)  # تبدیل مقدار قیمت به float
        description = f"اشتراک {plan.name}"  # توضیحات
        callback_url = request.build_absolute_uri('/payment/verify/')  # آدرس بازگشت

        # تعیین اینکه آیا از sandbox استفاده شود یا نه
        sandbox = settings.ZARINPAL_SANDBOX  # مقدار sandbox را از تنظیمات می‌گیریم

        # ارسال درخواست پرداخت با توجه به حالت sandbox
        payment_handler = ZarinPalPayment(merchant_id, amount, sandbox=sandbox)
        result = payment_handler.request_payment(callback_url, description, mobile=request.user.phone_number, email=request.user.email)
        print(result)
        if result.get('success') and result['data']:
            # ذخیره Authority برای تأیید پرداخت
            authority = result['data'].get('authority')
            payment_url = result['data'].get('payment_url')

            # ایجاد رکورد پرداخت
            payment = Payment.objects.create(
                user=request.user,
                plan=plan,
                authority=authority,
                amount=plan.price,
                status='pending'
            )
            request.session['payment_id'] = payment.id

            # ذخیره Authority برای تأیید پرداخت در سشن
            request.session['authority'] = authority
            request.session['plan_id'] = plan_id

            # هدایت به درگاه پرداخت
            return redirect(payment_url)
        else:
            # خطای 422 یا هر نوع خطای دیگر
            error_message = result.get('response_data', {}).get('data', {}).get('message', 'خطا در اتصال به درگاه پرداخت.')
            messages.error(request, error_message)
            return redirect('subscription_plans')
    except Exception as e:
        print(f"Error: {e}")
        messages.error(request, f"یک خطا رخ داد: {str(e)}")
        return redirect('subscription_plans')




@login_required
def verify_payment(request):
    authority = request.GET.get('Authority')  # کد Authority از درگاه
    if not authority:
        return render(request, 'payment/payment_failed.html', {'message': "کد Authority ارسال نشده است."})

    try:
        # بازیابی پلن از سشن
        plan_id = request.session.get('plan_id')
        if not plan_id:
            return render(request, 'payment/payment_failed.html', {'message': "پلن انتخاب شده پیدا نشد."})

        plan = get_object_or_404(SubscriptionPlan, id=plan_id)

        # بررسی وضعیت پرداخت
        merchant_id = settings.ZARINPAL_MERCHANT_ID
        sandbox = settings.ZARINPAL_SANDBOX
        payment_handler = ZarinPalPayment(merchant_id, plan.price, sandbox=sandbox)
        verification_result = payment_handler.verify_payment(authority)
        
        print(f"verification_result: {verification_result}")  # برای بررسی لاگ
        payment_id = request.session.get('payment_id')
        payment = get_object_or_404(Payment, id=payment_id)
        if verification_result['success']:
            # پرداخت موفقیت‌آمیز
            user_subscription, created = UserSubscription.objects.get_or_create(
                user=request.user,
                defaults={'plan': plan}
            )

            # تنظیم تاریخ‌ها
            if created:
                user_subscription.start_date = now()
            else:
                if user_subscription.start_date is None:
                    user_subscription.start_date = now()

            user_subscription.end_date = user_subscription.start_date + timedelta(days=365)
            user_subscription.save()
            ref_id = verification_result['response_data']['data'].get('ref_id')
            payment.status = 'paid'
            payment.ref_id = ref_id
            payment.verified_at = now()
            payment.save()

            return render(request, 'payment/payment_success.html', {
                'message': 'پرداخت شما با موفقیت انجام شد و اشتراک فعال گردید.'
            })
        else:
            payment.status = 'failed'
            payment.save()
            return render(request, 'payment/payment_failed.html', {'message': 'پرداخت انجام نشد.'})
    except Exception as e:
        return render(request, 'payment/payment_failed.html', {'message': f"یک خطا رخ داد: {str(e)}"})



@login_required
def payment_history(request):
    payments = Payment.objects.filter(user=request.user).order_by('-created_at')
    print(payments)
    return render(request, 'payment/history.html', {'payments': payments})






@login_required
def my_subscription(request):
    subscription = UserSubscription.objects.get(user=request.user)
    return render(request, 'my_subscription.html', {'subscription': subscription})








def consultants_chat(request):
    if not request.user.is_authenticated:
        return redirect('login')
    page_title = "پشتیبانی کاربران"
    # دریافت چت‌های فعال برای کاربر
    active_sessions = ChatSession.objects.filter(consultant=request.user, is_active=True)
    chat_sessions = []
    for session in active_sessions:
        chat_sessions.append({
            'id': session.id,
            'user': session.user.username,
            'unread_count': session.get_unread_count(request.user)
        })
    return render(request, 'consultants_chat.html', {
        'active_sessions': chat_sessions,
        'user': request.user
    })

    







#api viewes




@api_view(['POST'])
def login_view(request):
    username = request.data.get('username')
    password = request.data.get('password')
    device_id = request.META.get('HTTP_X_DEVICE_ID')  # دریافت شناسه دستگاه از هدر درخواست

    if not device_id:
        return Response({"login_status": "failed", "error": "Device ID is required."}, status=400)

    user = authenticate(username=username, password=password)
    if user is not None:
        # بررسی اینکه آیا کاربر قبلاً از دستگاه دیگری وارد شده است
        if user.hardware_id and user.hardware_id != device_id:
            return Response({
                "login_status": "failed",
                "error": "این شماره در حال حاضر روی دستگاه دیگری فعال است. لطفاً برای راهنمایی بیشتر با پشتیبانی تماس بگیرید.",
                "support": {
                    "telegram": "@ecupars",
                    "instagram": "@ecupars"
                }
            }, status=403)

        # اگر کاربر از دستگاه جدید وارد می‌شود، hardware_id را به‌روزرسانی کنید
        user.hardware_id = device_id
        user.save()

        # تولید OTP و ذخیره Session
        otp = str(random.randint(100000, 999999))
        session = LoginSession.objects.create(user=user, otp=otp)

        # ارسال پاسخ
        return Response({
            "login_status": "pending",
            "session_id": str(session.session_id),
            "otp": otp  # این فقط برای تست است، در حالت واقعی باید OTP به کاربر ارسال شود.
        })

    return Response({"login_status": "failed", "error": "Invalid username or password."}, status=400)



@api_view(['POST'])
def webapp_login_view(request):
    username = request.data.get('username')
    password = request.data.get('password')
    device_id = request.META.get('HTTP_X_DEVICE_ID')  # دریافت شناسه دستگاه از هدر درخواست

    # if not device_id:
    #     return Response({"login_status": "failed", "error": "Device ID is required."}, status=400)

    user = authenticate(username=username, password=password)
    if user is not None:
        # بررسی اینکه آیا کاربر قبلاً از دستگاه دیگری وارد شده است
        if user.hardware_id and user.hardware_id != device_id:
            return Response({
                "login_status": "failed",
                "error": "این شماره در حال حاضر روی دستگاه دیگری فعال است. لطفاً برای راهنمایی بیشتر با پشتیبانی تماس بگیرید.",
                "support": {
                    "telegram": "@ecupars",
                    "instagram": "@ecupars"
                }
            }, status=403)

        # اگر کاربر از دستگاه جدید وارد می‌شود، hardware_id را به‌روزرسانی کنید
        user.hardware_id = device_id
        user.save()

        # تولید OTP و ذخیره Session
        otp = str(random.randint(100000, 999999))
        session = LoginSession.objects.create(user=user, otp=otp)

        # ارسال پاسخ
        return Response({
            "login_status": "pending",
            "session_id": str(session.session_id),
            "otp": otp  # این فقط برای تست است، در حالت واقعی باید OTP به کاربر ارسال شود.
        })

    return Response({"login_status": "failed", "error": "Invalid username or password."}, status=400)




@api_view(['POST'])
def verify_otp_view(request):
    session_id = request.data.get('session_id')
    otp = request.data.get('otp')

    try:
        session = LoginSession.objects.get(session_id=session_id)
        if session.otp == otp:
            session.is_verified = True
            session.save()

            # لاگین کردن کاربر
            login(request, session.user)  # کاربر را در سیستم لاگین کنید

            refresh = RefreshToken.for_user(session.user)

            return Response({
                "login_status": "success",
                "access_token": str(refresh.access_token),   
                "refresh_token": str(refresh),            
            })

        return Response({"login_status": "failed", "error": "Invalid OTP."}, status=400)
    except LoginSession.DoesNotExist:
        return Response({"login_status": "failed", "error": "Session not found."}, status=400)



#استثناهای سفارشی
class NoCategoryAccessException(APIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "شما به این دسته‌بندی دسترسی ندارید."
    default_code = "no_category_access"

class NoIssueAccessException(APIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "شما به این خطا دسترسی ندارید."
    default_code = "no_issue_access"

class NoDiagnosticAccessException(APIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "شما به مراحل عیب‌یابی دسترسی ندارید."
    default_code = "no_diagnostic_access"

class NoDeviceAccessException(APIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "شما با این دستگاه دسترسی ندارید."
    default_code = "no_device_access"



# پرمیشن سفارشی

class HasCategoryAccess(BasePermission):
    def has_permission(self, request, view):
        category_id = view.kwargs.get('cat_id')
        if not category_id:
            raise NoCategoryAccessException()

        user = request.user
        if not user.is_authenticated:
            raise NoCategoryAccessException()

        subscription = getattr(user, 'subscription', None)
        if not subscription:
            raise NoCategoryAccessException()

        if subscription.plan.access_to_all_categories:
            return True

        restricted_categories = subscription.plan.restricted_categories.all()
        if int(category_id) not in [cat.id for cat in restricted_categories]:
            raise NoCategoryAccessException()

        return True

class HasIssueAccess(BasePermission):
    def has_permission(self, request, view):
        issue_id = view.kwargs.get('issue_id')
        issue = get_object_or_404(Issue, id=issue_id)

        category_id = issue.category
        if not category_id:
            raise NoIssueAccessException()

        subscription = getattr(request.user, 'subscription', None)
        if not subscription:
            raise NoIssueAccessException()

        if subscription.plan.access_to_all_categories:
            return True

        restricted_categories = subscription.plan.restricted_categories.all()
        if int(category_id) not in [cat.id for cat in restricted_categories]:
            raise NoIssueAccessException()

        return True

class HasDiagnosticAccess(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not user.is_authenticated or not hasattr(user, 'subscription'):
            raise NoDiagnosticAccessException()

        subscription = user.subscription
        if not subscription.plan.access_to_diagnostic_steps:
            raise NoDiagnosticAccessException()

        return True

class HasDeviceAccess(BasePermission):
    def has_permission(self, request, view):
        device_id = request.META.get('HTTP_X_DEVICE_ID')
        if not device_id:
            raise NoDeviceAccessException()

        user = request.user
        if not user.is_authenticated:
            raise NoDeviceAccessException()

        if user.hardware_id != device_id:
            raise NoDeviceAccessException()

        return True




    

class HomeAPIView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    
    def get(self, request, *args, **kwargs):
        logger.info(f"User {request.user} accessed the car list.")  # ثبت لاگ دسترسی
        try:
            cars = IssueCategory.objects.filter(parent_category__isnull=True)
            logger.debug(f"Fetched {cars.count()} cars.")  # ثبت لاگ دیباگ
            serializer = IssueCategorySerializer(cars, many=True)
            response = Response({'cars': serializer.data})
            response['Content-Type'] = 'application/json; charset=utf-8'
            return response
        except Exception as e:
            logger.error(f"Error fetching car list: {e}")  # ثبت لاگ خطا
            return Response({'error': 'Unable to fetch car list.'}, status=500)


class UserCarDetail(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, HasCategoryAccess, HasDeviceAccess]

    def get(self, request, cat_id):
        logger.info(f"User {request.user} accessed car details for ID {cat_id}.")

        # گرفتن پارامترهای URL
        include_issues = request.query_params.get('include_issues', 'true').lower() == 'true'
        include_related_categories = request.query_params.get('include_related_categories', 'true').lower() == 'true'
        include_articles = request.query_params.get('include_articles', 'true').lower() == 'true'  # پارامتر جدید
        include_maps = request.query_params.get('include_maps', 'true').lower() == 'true'  # پارامتر جدید

        try:
            # پیدا کردن دسته‌بندی اصلی
            category = IssueCategory.objects.get(id=cat_id)
            category_serializer = IssueCategorySerializer(category)

            response_data = {
                "status": "success",
                "category": category_serializer.data,
            }

            # افزودن زیردسته‌ها اگر درخواست شده باشد
            if include_related_categories:
                subcategories = IssueCategory.objects.filter(parent_category=category)
                subcategories_serializer = IssueCategorySerializer(subcategories, many=True)
                response_data["related_categories"] = subcategories_serializer.data

            # افزودن خطاها اگر درخواست شده باشد
            if include_issues:
                issues = Issue.objects.filter(category=cat_id)
                issues_serializer = IssueSerializer(issues, many=True)
                response_data["issues"] = issues_serializer.data

            # افزودن مقالات اگر درخواست شده باشد
            if include_articles:
                articles = Article.objects.filter(category=cat_id)
                articles_serializer = ArticleSerializer(articles, many=True)
                response_data["articles"] = articles_serializer.data

            # افزودن نقشه‌ها اگر درخواست شده باشد
            if include_maps:
                maps = Map.objects.filter(category=cat_id)
                maps_serializer = MapSerializer(maps, many=True)
                response_data["maps"] = maps_serializer.data

            logger.debug(f"Category {cat_id} returned with filters: include_issues={include_issues}, include_related_categories={include_related_categories}, include_articles={include_articles}, include_maps={include_maps}")

            response = Response(response_data)
            response['Content-Type'] = 'application/json; charset=utf-8'
            return response

        except IssueCategory.DoesNotExist:
            logger.warning(f"Category with ID {cat_id} not found.")
            return Response({'status': 'error', 'message': 'Category not found.'}, status=404)

        except ValueError as ve:
            logger.error(f"ValueError occurred for category ID {cat_id}: {ve}")
            return Response({'status': 'error', 'message': 'Invalid input provided.'}, status=400)

        except Exception as e:
            logger.error(f"Unexpected error for category ID {cat_id}: {e}")
            return Response({'status': 'error', 'message': 'An unexpected error occurred.'}, status=500)





class UserIssueDetailView(generics.RetrieveAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, HasIssueAccess, HasDeviceAccess]
    

    def get(self, request, issue_id):
        
        issue = Issue.objects.get(id=issue_id)
        
        issues_serializer = IssueSerializer(issue)
        response_data = {
                "status": "success",
                "issue": issues_serializer.data,
            }
        # اگر خطا سوال مرتبط داشته باشد
        if issue.question:
            question_data = QuestionSerializer(issue.question).data

            # اطلاعات گزینه‌ها با اضافه کردن مقصد هر گزینه
            
            options_data = [
                    {
                        'id': option.id,
                        'text': option.text,
                        'next_step': option.next_step.id if option.next_step else None,
                        'issue': option.issue.id if option.issue else None,
                        'article': option.article.id if option.article else None,
                    }
                    for option in issue.question.options.all()
            ]   

            # افزودن سوال و گزینه‌ها به پاسخ
            response_data.update({
                'question': question_data,
                'options': options_data,
            })
        response = Response(response_data)
        response['Content-Type'] = 'application/json; charset=utf-8'
        return response





class UserStepDetail(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, HasDiagnosticAccess, HasDeviceAccess]
    def get(self, request, step_id):
        step = DiagnosticStep.objects.get(id=step_id)
        question = step.question
        options = question.options.all() if question else []

        # اطلاعات نقشه
        map_data = None
        if step.map:
            map_data = {
                "title": step.map.title,  # عنوان نقشه
                "url": step.map.image.url if step.map.image else None,  # لینک تصویر نقشه
            }

        response_data = {
            "step": {
                "id": step.id,
                "title": step.solution.title if step.solution else None,
                "description": step.solution.description if step.solution else None,
                "letter": step.letter,
                "map": map_data,  # ارسال عنوان و URL نقشه
            },
            "question": {
                    "id": question.id if question else None,
                    "text": question.text if question else None,
                } if question else None,
            "options": [
                {
                    "id": option.id,
                    "text": option.text,
                    "next_step": option.next_step.id if option.next_step else None,
                    "issue": option.issue.id if option.issue else None,
                    "atricle": option.article.id if option.article else None,
                }
                for option in options
            ],
        }
        response = Response(response_data)
        response['Content-Type'] = 'application/json; charset=utf-8'
        return response


# لیست پلن‌های اشتراکی
class SubscriptionPlanListView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    def get(self, request):
        plans = SubscriptionPlan.objects.all()
        serializer = SubscriptionPlanSerializer(plans, many=True)
        

        response = Response(serializer.data)
        response['Content-Type'] = 'application/json; charset=utf-8'
        return response





# فعال‌سازی اشتراک
class ActivateSubscriptionView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        plan_id = request.data.get("plan_id")
        try:
            plan = SubscriptionPlan.objects.get(id=plan_id)
        except SubscriptionPlan.DoesNotExist:
            return Response({"error": "Plan not found."}, status=status.HTTP_404_NOT_FOUND)

        user_subscription, created = UserSubscription.objects.update_or_create(
            user=request.user,
            defaults={
                "plan": plan,
                "start_date": now(),
                "end_date": now() + timedelta(days=30),
            }
        )
        user_subscription.active_categories.set(plan.access_to_categories.all())
        user_subscription.save()

        return Response({"message": "Subscription activated successfully."}, status=status.HTTP_200_OK)




# مشاهده اطلاعات اشتراک کاربر
class UserSubscriptionView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            subscription = UserSubscription.objects.get(user=request.user)
            serializer = UserSubscriptionSerializer(subscription)

            response = Response(serializer.data)
            response['Content-Type'] = 'application/json; charset=utf-8'
            return response
        except UserSubscription.DoesNotExist:
            return Response({"error": "No active subscription found."}, status=status.HTTP_404_NOT_FOUND)
            



class AdvertisementListView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    def get(self, request):
        try:
            advertisements = Advertisement.objects.all()
            serializer = AdvertisementSerializer(advertisements, many=True)
            logger.info(f"User {request.user} fetched advertisements.")
            response = Response(serializer.data)
            response['Content-Type'] = 'application/json; charset=utf-8'
            return response

        except Exception as e:
            logger.error(f"Error fetching advertisements: {e}")
            return Response({'error': 'Unable to fetch advertisements.'}, status=500)



class OptionListView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, HasDiagnosticAccess, HasDeviceAccess]
    def get(self, request):
        try:
            options = Option.objects.all()
            serializer = OptionSerializer(options, many=True)
            logger.info(f"User {request.user} fetched options.")

            response = Response(serializer.data)
            response['Content-Type'] = 'application/json; charset=utf-8'
            return response

        except Exception as e:
            logger.error(f"Error fetching options: {e}")
            return Response({'error': 'Unable to fetch options.'}, status=500)


class StartChatView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        
        # بررسی وجود چت‌سشن فعال برای کاربر
        session = ChatSession.objects.filter(user=user, is_active=True).first()

        if session:
            response = Response(ChatSessionSerializer(session).data)
            response['Content-Type'] = 'application/json; charset=utf-8'
            return response

        # اختصاص مشاور
        User = get_user_model()
        consultant = User.objects.filter(groups__name='Consultants').first()
        if not consultant:
            return Response({'error': 'No consultants available'}, status=503)

        # ایجاد چت‌سشن جدید
        session = ChatSession.objects.create(user=user, consultant=consultant)

        # ایجاد UserChatSession برای کاربر و مشاور
        UserChatSession.objects.create(user=user, chat_session=session, unread_messages_count=0)
        UserChatSession.objects.create(user=consultant, chat_session=session, unread_messages_count=0)

        # بازگرداندن پاسخ
        response = Response(ChatSessionSerializer(session).data)
        response['Content-Type'] = 'application/json; charset=utf-8'
        return response





class ChatMessagesAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, session_id):
        # فیلتر کردن پیام‌ها بر اساس session_id
        messages = Message.objects.filter(session_id=session_id).order_by('timestamp')

        # اگر هیچ پیامی وجود نداشت
        if not messages:
            return Response({'detail': 'No messages found for this session.'}, status=status.HTTP_404_NOT_FOUND)

        # سریالایزر کردن پیام‌ها
        serializer = MessageSerializer(messages, many=True)

        # بازگشت داده‌ها به صورت پاسخ
        return Response(serializer.data)


class SendMessageView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, session_id):
        message_content = request.data.get('message')
        sender_id = request.data.get('sender_id')
        User = get_user_model()
        try:
            session = ChatSession.objects.get(id=session_id)
            sender = User.objects.get(id=sender_id)

            # ذخیره پیام در دیتابیس
            message = Message.objects.create(session=session, sender=sender, content=message_content)

            # Broadcast message to the user via WebSocket
            # اینجا می‌توانید از کانال‌ها برای ارسال پیام به کاربر استفاده کنید

            return Response({'status': 'success', 'message_id': message.id})

        except ChatSession.DoesNotExist:
            return Response({'error': 'Chat session does not exist'}, status=404)
        except User.DoesNotExist:
            return Response({'error': 'User does not exist'}, status=404)


class CloseChatView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, session_id):
        try:
            session = ChatSession.objects.get(id=session_id, user=request.user)
            session.close_chat()
            return Response({'status': 'success', 'message': 'Chat closed successfully'})
        except ChatSession.DoesNotExist:
            return Response({'error': 'Chat session does not exist'}, status=404)



class MarkMessagesAsReadView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, session_id):
        try:
            session = ChatSession.objects.get(id=session_id)
            current_user = request.user

            messages = Message.objects.filter(session=session).exclude(sender=current_user)
            for message in messages:
                message.mark_as_read(current_user)

            user_chat_session = UserChatSession.objects.get_or_create(user=current_user, chat_session=session)
            user_chat_session = user_chat_session[0]
            user_chat_session.update_unread_count()

            # به‌روزرسانی تعداد پیام‌های خوانده نشده برای کاربر مقابل
            if current_user == session.user:
                
                recipient = session.consultant
            else:
                recipient = session.user

            recipient_user_chat_session = UserChatSession.objects.get(user=recipient, chat_session=session)
            
            recipient_user_chat_session.update_unread_count()
            print(recipient_user_chat_session.unread_messages_count)

            return Response({'status': 'success', 'message': 'Messages marked as read.'})

        except ChatSession.DoesNotExist:
            return Response({'error': 'Chat session does not exist'}, status=404)



class ArticlePagination(LimitOffsetPagination):
    default_limit = 10
    max_limit = 100

class ArticleListAPIView(generics.ListAPIView):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    pagination_class = ArticlePagination




class PaymentRequestAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]        

    def post(self, request):
        serializer = PaymentRequestSerializer(data=request.data)
        if serializer.is_valid():
            plan_id = serializer.validated_data['plan_id']
            user_phone = serializer.validated_data['user_phone']
            user_email = serializer.validated_data['user_email']
            discount_code = serializer.validated_data.get('discount_code')

            # پیدا کردن پلن انتخابی
            plan = get_object_or_404(SubscriptionPlan, id=plan_id)

            # محاسبه مبلغ نهایی با اعمال تخفیف
            final_amount = float(plan.price)
            discount_message = None

            if discount_code:
                try:
                    # بررسی کد تخفیف
                    discount = DiscountCode.objects.get(
                        code=discount_code,
                        user=request.user,  # کاربر احراز هویت شده
                        expiration_date__gte=timezone.now(),
                    )
                    # بررسی تعداد استفاده
                    if discount.max_usage and discount.usage_count >= discount.max_usage:
                        return Response({'error': 'تعداد مجاز استفاده از این کد تخفیف به پایان رسیده است.'}, status=status.HTTP_400_BAD_REQUEST)

                    # اعمال تخفیف
                    final_amount = final_amount * (1 - discount.discount_percentage / 100)
                    discount_message = f"تخفیف {discount.discount_percentage}% اعمال شد."

                    # افزایش تعداد استفاده از کد تخفیف
                    discount.usage_count += 1
                    discount.save()

                except DiscountCode.DoesNotExist:
                    return Response({'error': 'کد تخفیف نامعتبر است.'}, status=status.HTTP_400_BAD_REQUEST)

            # اگر قیمت پلن صفر باشد (رایگان)
            if final_amount == 0:
                user_subscription, created = UserSubscription.objects.get_or_create(
                    user=request.user,
                    defaults={'plan': plan}
                )
                if created:
                    user_subscription.start_date = timezone.now()
                user_subscription.end_date = user_subscription.start_date + timedelta(days=30)
                user_subscription.save()

                return Response({'message': 'اشتراک رایگان شما با موفقیت فعال شد.'}, status=status.HTTP_200_OK)

            # اگر قیمت پلن غیر از صفر باشد، درخواست پرداخت زرین‌پال را ارسال می‌کنیم
            merchant_id = settings.ZARINPAL_MERCHANT_ID
            description = f"اشتراک {plan.name}"
            callback_url = request.build_absolute_uri('/payment/verify/')
            sandbox = settings.ZARINPAL_SANDBOX
            payment_handler = ZarinPalPayment(merchant_id, final_amount, sandbox=sandbox)
            result = payment_handler.request_payment(callback_url, description, mobile=user_phone, email=user_email)
            
            if result.get('success') and result['data']:
                authority = result['data'].get('authority')
                payment_url = result['data'].get('payment_url')

                # ایجاد رکورد پرداخت
                payment = Payment.objects.create(
                    user=request.user,
                    plan=plan,
                    authority=authority,
                    amount=final_amount,
                    status='pending',
                    discount_code=discount_code if discount_code else None
                )

                # ذخیره اطلاعات در سشن
                request.session['authority'] = authority
                request.session['plan_id'] = plan_id
                request.session['payment_id'] = payment.id

                response_data = {
                    'payment_url': payment_url,
                    'payment_id': payment.id,
                    'final_amount': final_amount,
                }
                if discount_message:
                    response_data['discount_message'] = discount_message

                return Response(response_data, status=status.HTTP_200_OK)
            else:
                error_message = result.get('response_data', {}).get('data', {}).get('message', 'خطا در اتصال به درگاه پرداخت.')
                return Response({'error': error_message}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




class PaymentVerificationAPIView(APIView):
    def get(self, request):  # زرین‌پال از متد GET برای callback استفاده می‌کند
        authority = request.GET.get('Authority')  # دریافت Authority از URL
        if not authority:
            return render(request, 'payment/payment_failed.html', {'message': "کد Authority ارسال نشده است."})

        try:
            # پیدا کردن رکورد پرداخت بر اساس Authority
            payment = Payment.objects.get(authority=authority)
            plan = payment.plan

            # بررسی وضعیت پرداخت
            merchant_id = settings.ZARINPAL_MERCHANT_ID
            sandbox = settings.ZARINPAL_SANDBOX
            payment_handler = ZarinPalPayment(merchant_id, plan.price, sandbox=sandbox)
            verification_result = payment_handler.verify_payment(authority)

            if verification_result.get('success') and verification_result.get('data', {}).get('code') == 101:
                # پرداخت موفقیت‌آمیز
                user_subscription, created = UserSubscription.objects.get_or_create(
                    user=payment.user,
                    defaults={'plan': plan}
                )

                if created:
                    user_subscription.start_date = now()
                user_subscription.end_date = user_subscription.start_date + timedelta(days=365)
                user_subscription.save()

                # به‌روزرسانی رکورد پرداخت
                payment.status = 'paid'
                payment.ref_id = verification_result['data'].get('ref_id')
                payment.verified_at = now()
                payment.save()

                return render(request, 'payment/payment_success.html', {
                    'message': 'پرداخت شما با موفقیت انجام شد و اشتراک فعال گردید.'
                })
            else:
                # پرداخت ناموفق
                payment.status = 'failed'
                payment.save()

                return render(request, 'payment/payment_failed.html', {'message': 'پرداخت انجام نشد.'})
        except Payment.DoesNotExist:
            return render(request, 'payment/payment_failed.html', {'message': 'پرداخت پیدا نشد.'})




class PaymentStatusAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]  # فقط کاربران احراز هویت شده می‌توانند از این ویو استفاده کنند

    def get(self, request):
        payment_id = request.query_params.get('payment_id')
        if not payment_id:
            return Response({'error': 'payment_id ارسال نشده است.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            payment = Payment.objects.get(id=payment_id)
            # بررسی اینکه پرداخت متعلق به کاربر فعلی است
            if payment.user != request.user:
                return Response({'error': 'شما مجاز به مشاهده این پرداخت نیستید.'}, status=status.HTTP_403_FORBIDDEN)

            return Response({
                'status': payment.status,
                'ref_id': payment.ref_id,
                'verified_at': payment.verified_at,
            }, status=status.HTTP_200_OK)
        except Payment.DoesNotExist:
            return Response({'error': 'پرداخت پیدا نشد.'}, status=status.HTTP_404_NOT_FOUND)





@api_view(['POST'])
def send_otp(request):
    phone_number = request.data.get('phone_number')
    first_name = request.data.get('first_name')
    last_name = request.data.get('last_name')
    car_brand = request.data.get('car_brand')
    city = request.data.get('city')
    hardware_id = request.data.get('hardware_id')
    referrer_code = request.data.get('referrer_code')

    if not phone_number:
        return Response({"error": "شماره تماس الزامی است."}, status=status.HTTP_400_BAD_REQUEST)

    if CustomUser.objects.filter(phone_number=phone_number).exists():
        return Response({"error": "این شماره تماس قبلاً ثبت‌نام شده است."}, status=status.HTTP_400_BAD_REQUEST)

    # بررسی کد معرف
    referrer = None
    if referrer_code:
        try:
            referral_code_instance = ReferralCode.objects.get(code=referrer_code)
            referrer = referral_code_instance.user
        except ReferralCode.DoesNotExist:
            return Response({"error": "کد معرف معتبر نیست."}, status=status.HTTP_400_BAD_REQUEST)

    # تولید OTP
    otp = str(random.randint(100000, 999999))

    # ذخیره موقت اطلاعات
    cache_key = f"signup_data_{phone_number}"
    cache.set(cache_key, {
        "first_name": first_name,
        "last_name": last_name,
        "car_brand": car_brand,
        "city": city,
        "hardware_id": hardware_id,
        "referrer_code": referrer_code,
        "otp": otp,
    }, timeout=120)  # 2 دقیقه

    # ارسال پیامک
    otp_id = 1145
    replace_tokens = [otp]
    sms_result = send_pattern_sms(otp_id, replace_tokens, phone_number)
    
    if not sms_result['success']:  # بررسی موفقیت ارسال پیامک
        cache.delete(cache_key)  # حذف داده‌های کش در صورت خطا
        return Response({
            "error": "خطا در ارسال پیامک",
            "sms_details": sms_result['message']
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # ارسال پاسخ موفقیت‌آمیز
    return Response({
        "message": "OTP ارسال شد.",
        "sms_result": sms_result
    })




@api_view(['POST'])
def resend_otp(request):
    phone_number = request.data.get('phone_number')
    if not phone_number:
        return Response({"error": "شماره تماس الزامی است."}, status=status.HTTP_400_BAD_REQUEST)

    # بررسی وجود OTP در کش
    cache_key = f"signup_data_{phone_number}"
    cached_data = cache.get(cache_key)
    if not cached_data:
        return Response({"error": "لطفاً ابتدا درخواست OTP بدهید."}, status=status.HTTP_400_BAD_REQUEST)

    # تولید OTP جدید
    otp = str(random.randint(100000, 999999))
    cached_data["otp"] = otp
    cache.set(cache_key, cached_data, timeout=120)  # ذخیره OTP جدید در کش

    # ارسال OTP جدید
    otp_id = 1145  # شناسه پترن
    replace_tokens = [otp]
    sms_result = send_pattern_sms(otp_id, replace_tokens, phone_number)

    if sms_result["success"]:
        return Response({"message": "کد OTP مجدداً ارسال شد."})
    else:
        return Response({"error": "خطا در ارسال مجدد کد OTP."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




@api_view(['POST'])
def verify_otp_and_signup(request):
    phone_number = request.data.get('phone_number')
    otp = request.data.get('otp')
    password = request.data.get('password')

    if not phone_number or not otp or not password:
        return Response({"error": "شماره تماس، کد OTP و رمز عبور الزامی هستند."}, status=status.HTTP_400_BAD_REQUEST)

    # بازیابی اطلاعات موقت از کش
    cache_key = f"otp_{phone_number}"
    cached_data = cache.get(cache_key)

    if not cached_data:
        return Response({"error": "کد OTP منقضی شده یا وجود ندارد."}, status=status.HTTP_400_BAD_REQUEST)

    if cached_data["otp"] == otp:
        # OTP معتبر است
        # حذف اطلاعات موقت از کش پس از تأیید
        cache.delete(cache_key)

        # ایجاد کاربر جدید
        user = CustomUser.objects.create_user(
            username=phone_number,  # استفاده از شماره تماس به عنوان نام کاربری
            phone_number=phone_number,
            first_name=cached_data["first_name"],
            last_name=cached_data["last_name"],
            password=password,
            city=cached_data["city"],
            car_brand=cached_data["car_brand"],
            hardware_id=cached_data["hardware_id"],
        )

        # ایجاد کد معرفی برای کاربر جدید
        ReferralCode.objects.create(user=user, code=phone_number)  # استفاده از شماره تماس به عنوان کد معرفی

        # ایجاد رابطه معرفی (اگر کد معرف وجود داشته باشد)
        referrer_code = cached_data.get("referrer_code")
        if referrer_code:
            try:
                referral_code_instance = ReferralCode.objects.get(code=referrer_code)
                referrer = referral_code_instance.user
                UserReferral.objects.create(referrer=referrer, referred_user=user)
            except ReferralCode.DoesNotExist:
                # اگر کد معرف وجود نداشته باشد، خطا نمی‌دهیم (اختیاری است)
                pass

        # لاگین کردن کاربر
        login(request, user)  # کاربر را در سیستم لاگین کنید

        # ایجاد توکن‌ها
        refresh = RefreshToken.for_user(user)

        return Response({
            "message": "ثبت‌نام با موفقیت انجام شد.",
            "access_token": str(refresh.access_token),
            "refresh_token": str(refresh),
        })

    else:
        return Response({"error": "کد OTP نامعتبر است."}, status=status.HTTP_400_BAD_REQUEST)
    


class ReferralCodeDetailAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        try:
            # پیدا کردن کاربر با user_id
            user = CustomUser.objects.get(id=user_id)
            
            # پیدا کردن کد رفرال کاربر
            referral_code = ReferralCode.objects.get(user=user)
            
            # پیدا کردن کاربرانی که از این کد رفرال ارجاع شده‌اند
            referred_users = UserReferral.objects.filter(referrer=user)
            referred_user_data = []
            
            for referred_user in referred_users:
                subscriptions = UserSubscription.objects.filter(user=referred_user.referred_user)
                subscription_details = [
                    {
                        'plan_name': subscription.plan.name,
                        'purchase_date': subscription.start_date,
                        'amount_paid': subscription.plan.price,
                    } for subscription in subscriptions
                ]
                referred_user_data.append({
                    'user_id': referred_user.referred_user.id,
                    'referral_code': referral_code.code,
                    'subscriptions': subscription_details
                })

            return Response({
                'referral_code': referral_code.code,
                'referred_users': referred_user_data
            }, status=status.HTTP_200_OK)
        
        except CustomUser.DoesNotExist:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
        
        except ReferralCode.DoesNotExist:
            return Response({'error': 'Referral code not found.'}, status=status.HTTP_404_NOT_FOUND)
        


class DiscountCodeDetailAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request, user_id):
        try:
            # پیدا کردن کاربر با user_id
            user = CustomUser.objects.get(id=user_id)
            
            # گرفتن تمامی کدهای تخفیف کاربر
            discount_codes = DiscountCode.objects.filter(user=user)
            
            # جمع‌آوری داده‌ها برای ارسال
            discount_code_data = []
            
            for discount_code in discount_codes:
                # پیدا کردن کاربرانی که از این کد تخفیف استفاده کرده‌اند
                users_with_discount = CustomUser.objects.filter(Q(payment__discount_code=discount_code)).distinct()
                
                user_data = []
                for user_with_discount in users_with_discount:
                    # پیدا کردن اشتراک‌هایی که این کاربران خریداری کرده‌اند
                    subscriptions = UserSubscription.objects.filter(user=user_with_discount)
                    subscription_details = [
                        {
                            'plan_name': subscription.plan.name,
                            'purchase_date': subscription.start_date,
                            'amount_paid': subscription.plan.price,
                        } for subscription in subscriptions
                    ]
                    user_data.append({
                        'user_id': user_with_discount.id,
                        'username': user_with_discount.username,
                        'subscriptions': subscription_details
                    })
                
                # اضافه کردن اطلاعات کد تخفیف و کاربران استفاده‌کننده از آن
                discount_code_data.append({
                    'discount_code': discount_code.code,
                    'discount_percentage': discount_code.discount_percentage,
                    'expiration_date': discount_code.expiration_date,
                    'max_usage': discount_code.max_usage,
                    'usage_count': discount_code.usage_count,
                    'users_with_discount': user_data
                })
            
            return Response({
                'user_id': user.id,
                'discount_codes': discount_code_data
            }, status=status.HTTP_200_OK)
        
        except CustomUser.DoesNotExist:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)



class UserProfileAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            # پیدا کردن کاربر جاری
            user = request.user

            # اطلاعات پایه‌ای کاربر
            user_data = {
                'user_id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'phone_number': user.phone_number,
                'city': user.city,
                'job': user.job,
                'car_brand': user.get_car_brand_display(),
                'national_id': user.national_id,
            }

            # بررسی وجود پلن فعال برای کاربر
            try:
                subscription = UserSubscription.objects.get(user=user)
                subscription_data = {
                    'plan': {
                        'id': subscription.plan.id,
                        'name': subscription.plan.name,
                        'description': subscription.plan.description,
                        'price': str(subscription.plan.price),  # تبدیل به رشته برای جلوگیری از خطاهای سریال‌سازی
                    },
                    'active_categories': [
                        {
                            'id': category.id,
                            'name': category.name
                        }
                        for category in subscription.active_categories.all()
                    ],
                    'start_date': subscription.start_date,
                    'end_date': subscription.end_date,
                    'is_active': subscription.is_active(),
                }
                user_data['subscription'] = subscription_data
            except UserSubscription.DoesNotExist:
                user_data['subscription'] = None

            return Response(user_data, status=status.HTTP_200_OK)

        except CustomUser.DoesNotExist:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)




@csrf_exempt
def bulk_copy_maps(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        map_ids = data.get('map_ids', [])
        target_category_id = data.get('target_category_id')

        try:
            target_category = IssueCategory.objects.get(id=target_category_id)
            for map_id in map_ids:
                map_instance = Map.objects.get(id=map_id)
                # ایجاد یک کپی از نقشه
                new_map = Map.objects.create(
                    title=map_instance.title,
                    category=target_category,
                    # سایر فیلدها را نیز کپی کنید
                )
            return JsonResponse({'status': 'success', 'message': 'نقشه‌ها با موفقیت کپی شدند.'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'error', 'message': 'درخواست نامعتبر'})





class ArticleDetailView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, article_id):
        try:
            # پیدا کردن مقاله
            article = Article.objects.get(id=article_id)
            article_data = ArticleSerializer(article).data

            # ساخت پاسخ
            response_data = {
                "status": "success",
                "article": article_data,  # question به صورت خودکار در article_data وجود دارد
            }

            response = Response(response_data)
            response['Content-Type'] = 'application/json; charset=utf-8'
            return response

        except Article.DoesNotExist:
            return Response({"status": "error", "message": "مقاله یافت نشد."}, status=status.HTTP_404_NOT_FOUND)



class CategoryAPIView(APIView):
    def get(self, request):
        # دریافت تمام دسته‌های اصلی (دسته‌هایی که parent_category ندارند)
        main_categories = IssueCategory.objects.filter(parent_category__isnull=True)
        serializer = CategorySerializer(main_categories, many=True)
        return Response(serializer.data)