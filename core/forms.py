from django import forms
from .models import MapCategory, Map, IssueCategory, Issue, Solution, Subscription, Bookmark, DiagnosticStep, Question, Option, Tag, CustomUser
from django_ckeditor_5.widgets import CKEditor5Widget
from django.db.models import Count
from django.forms import BaseFormSet, formset_factory
from django.forms import modelformset_factory
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.hashers import make_password
from django_select2.forms import Select2TagWidget
import json
from django.core.exceptions import ValidationError
import ast
from django_select2.forms import Select2MultipleWidget
import re






def categories_without_subcategories():
    return IssueCategory.objects.annotate(num_subcategories=Count('subcategories')).filter(num_subcategories=0)

class IssueCategoryForm(forms.ModelForm):


    parent_category = forms.ModelChoiceField(
        queryset=IssueCategory.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False,
        label="سرگروه"
    )

    class Meta:
        model = IssueCategory
        fields = ['name', 'order', 'parent_category', 'logo']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'نام دسته بندی را وارد کنید'}),
            'parent_category': forms.Select(attrs={'class': 'form-control', 'blank': True}),
        }
        labels = {
            'name': 'نام دسته بندی',
            'logo':'لوگو دسته',
            'order':'ترتیب'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['parent_category'].label_from_instance = lambda obj: obj.get_full_category_name()

class IssueForm(forms.ModelForm):

    category = forms.ModelChoiceField(
        categories_without_subcategories(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True,
        label="دسته بندی"
    )

    tags = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'style': 'width: 100%;', 'placeholder': 'تگ‌ها را با ویرگول جدا کنید...'}),
        label='تگ‌ها'
    )

    question = forms.ModelChoiceField(
        queryset= Question.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='سوال'
    )



    class Meta:
        model = Issue
        fields = ['title','description','category']
        labels = {
            'title': 'عنوان خطا',
            'description': 'توضیحات',
            'category': 'دسته بندی',
        }
        widgets = {
            "description": CKEditor5Widget(
                attrs={"class": "django_ckeditor_5", "required": "false"}, config_name="extends"
            )
        }


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].label_from_instance = lambda obj: obj.get_full_category_name()
        if self.instance.pk:
            # استخراج تگ‌ها به صورت یک لیست
            raw_tags = self.instance.tags.values_list('name', flat=True)
            # تبدیل لیست تگ‌ها به رشته‌ای جدا شده با کاما
            tags_initial = ', '.join(raw_tags)  # تبدیل به فرمت مناسب
            self.fields['tags'].initial = tags_initial






    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()
            # پردازش ورودی تگ‌ها و اضافه کردن یا دریافت آن‌ها از دیتابیس
            tags_input = self.cleaned_data['tags']
            print("Tags input:", tags_input)
            tag_names = [name.strip() for name in tags_input.split(',') if name.strip()]
            tags = []
            for name in tag_names:
                tag, _ = Tag.objects.get_or_create(name=name)
                tags.append(tag)
            instance.tags.set(tags)  # اینجا تگ‌ها به درستی اضاف می‌شوند و دیگر نیازی به تغییر نیست

        return instance



class IssueCatForm(forms.ModelForm):
    tags = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'style': 'width: 100%;', 'placeholder': 'تگ‌ها را با ویرگول جدا کنید...'}),
        label='تگ‌ها'
    )

    class Meta:
        model = Issue
        fields = ['title', 'description']
        labels = {
            'title': 'عنوان خطا',
            'description': 'توضیحات'
        }
        widgets = {
            "description": CKEditor5Widget(
                attrs={"class": "django_ckeditor_5", "required": "false"}, config_name="extends"
            )
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            # استخراج تگ‌ها به صورت یک لیست
            raw_tags = self.instance.tags.values_list('name', flat=True)
            # تبدیل لیست تگ‌ها به رشته‌ای جدا شده با کاما
            tags_initial = ', '.join(raw_tags)  # تبدیل به فرمت مناسب
            self.fields['tags'].initial = tags_initial






    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()
            # پردازش ورودی تگ‌ها و اضافه کردن یا دریافت آن‌ها از دیتابیس
            tags_input = self.cleaned_data['tags']
            print("Tags input:", tags_input)
            tag_names = [name.strip() for name in tags_input.split(',') if name.strip()]
            tags = []
            for name in tag_names:
                tag, _ = Tag.objects.get_or_create(name=name)
                tags.append(tag)
            instance.tags.set(tags)  # اینجا تگ‌ها به درستی اضاف می‌شوند و دیگر نیازی به تغییر نیست

        return instance



















class SolutionForm(forms.ModelForm):
    issues = forms.ModelMultipleChoiceField(
        queryset=Issue.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'form-control', 'multiple': 'multiple'}),
        required=False,
        label='خطاها'
    )

    tags = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'style': 'width: 100%;', 'placeholder': 'تگ‌ها را با ویرگول جدا کنید...'}),
        label='تگ‌ها'
    )

    class Meta:
        model = Solution
        fields = ['title', 'description', 'issues', 'is_public']
        labels = {
            'title': 'عنوان راه حل',
            'description': 'توضیحات راه حل',
            'issues': 'خطاها',
            'is_public': 'عمومی'
        }
        widgets = {
            "description": CKEditor5Widget(
                attrs={"class": "django_ckeditor_5", "required": "false"}, config_name="extends"
            )
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            # استخراج تگ‌ها به صورت یک لیست
            raw_tags = self.instance.tags.values_list('name', flat=True)
            # تبدیل لیست تگ‌ها به رشته‌ای جدا شده با کاما
            tags_initial = ', '.join(raw_tags)  # تبدیل به فرمت مناسب
            self.fields['tags'].initial = tags_initial






    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()
            # پردازش ورودی تگ‌ها و اضافه کردن یا دریافت آن‌ها از دیتابیس
            tags_input = self.cleaned_data['tags']
            print("Tags input:", tags_input)
            tag_names = [name.strip() for name in tags_input.split(',') if name.strip()]
            tags = []
            for name in tag_names:
                tag, _ = Tag.objects.get_or_create(name=name)
                tags.append(tag)
            instance.tags.set(tags)  # اینجا تگ‌ها به درستی اضاف می‌شوند و دیگر نیازی به تغییر نیست

        return instance























class issue_SolutionForm(forms.ModelForm):
    tags = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'style': 'width: 100%;', 'placeholder': 'تگ‌ها را با ویرگول جدا کنید...'}),
        label='تگ‌ها'
    )


    class Meta:
        model = Solution
        fields = ['title', 'description']  
        labels = {
            'title': 'عنوان راه حل',
            'description': 'توضیحات راه حل',
        }

        widgets = {
            "description": CKEditor5Widget(
                attrs={"class": "django_ckeditor_5", "required": "false"}, config_name="extends"
            )
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            # استخراج تگ‌ها به صورت یک لیست
            raw_tags = self.instance.tags.values_list('name', flat=True)
            # تبدیل لیست تگ‌ها به رشته‌ای جدا شده با کاما
            tags_initial = ', '.join(raw_tags)  # تبدیل به فرمت مناسب
            self.fields['tags'].initial = tags_initial






    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()
            # پردازش ورودی تگ‌ها و اضافه کردن یا دریافت آن‌ها از دیتابیس
            tags_input = self.cleaned_data['tags']
            print("Tags input:", tags_input)
            tag_names = [name.strip() for name in tags_input.split(',') if name.strip()]
            tags = []
            for name in tag_names:
                tag, _ = Tag.objects.get_or_create(name=name)
                tags.append(tag)
            instance.tags.set(tags)  # اینجا تگ‌ها به درستی اضاف می‌شوند و دیگر نیازی به تغییر نیست

        return instance




class SubscriptionForm(forms.ModelForm):
    class Meta:
        model = Subscription
        fields = ['user', 'active', 'access_level' , 'expiry_date']
        widgets = {
            'user': forms.Select(attrs={'class': 'form-control'}),
            'expiry_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
        labels = {
            'user': 'کاربر',
            'active': 'فعال',
            'access_level': 'سطح دسترسی',
            'expiry_date': 'تاریخ انقضا',
        }

class BookmarkForm(forms.ModelForm):
    class Meta:
        model = Bookmark
        fields = ['url', 'title']
        widgets = {
            'url': forms.HiddenInput(),
            'title': forms.HiddenInput(),
        }
        labels = {
            'url': 'آدرس صفحه',
            'title': 'عنوان',
        }


class DiagnosticStepForm(forms.ModelForm):
    class Meta:
        model = DiagnosticStep
        fields = ['solution', 'question','has_cycle']

        labels = {
            'solution': 'راهکار',
            'question': 'سوال',
            'has_cycle': 'برگشت به ابتدا'
        }
        






class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['text']

        labels = {
            'text': 'متن سوال',
        }



class OptionForm(forms.ModelForm):
    next_step = forms.ModelChoiceField(
        queryset= Solution.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False,
        label='مرحله بعدی'
    )
    class Meta:
        model = Option
        fields = ['text', 'question', 'next_step']



class TagForm(forms.ModelForm):
    class Meta:
        model = Tag
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'نام تگ را وارد کنید'}),
        }


class UserForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name','username', 'email', 'password', 'role']
        labels = {
            'role': 'نوع کاربر',

        }

    def save(self, commit=True):
        # ابتدا از متد save والد صدا می‌زنیم
        user = super().save(commit=False)

        # اگر پسورد تغییر کرده باشد، آن را هش می‌کنیم
        if self.cleaned_data['password']:
            user.password = make_password(self.cleaned_data['password'])
        
        if commit:
            user.save()
        return user


class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = CustomUser  # Use your custom user model
        fields = ('first_name', 'last_name','username', 'email', 'password1', 'password2')  # Adjust fields as necessary












class MapForm(forms.ModelForm):
    tags = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'style': 'width: 100%;', 'placeholder': 'تگ‌ها را با ویرگول جدا کنید...'}),
        label='تگ‌ها'
    )


    class Meta:
        model = Map
        fields = ['title', 'image']  
        labels = {
            'title': 'عنوان ',
            'image': 'تصویر ',
        }


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            # استخراج تگ‌ها به صورت یک لیست
            raw_tags = self.instance.tags.values_list('name', flat=True)
            # تبدیل لیست تگ‌ها به رشته‌ای جدا شده با کاما
            tags_initial = ', '.join(raw_tags)  # تبدیل به فرمت مناسب
            self.fields['tags'].initial = tags_initial






    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()
            # پردازش ورودی تگ‌ها و اضافه کردن یا دریافت آن‌ها از دیتابیس
            tags_input = self.cleaned_data['tags']
            print("Tags input:", tags_input)
            tag_names = [name.strip() for name in tags_input.split(',') if name.strip()]
            tags = []
            for name in tag_names:
                tag, _ = Tag.objects.get_or_create(name=name)
                tags.append(tag)
            instance.tags.set(tags)  # اینجا تگ‌ها به درستی اضاف می‌شوند و دیگر نیازی به تغییر نیست

        return instance



class MapCategoryForm(forms.ModelForm):


    parent_category = forms.ModelChoiceField(
        queryset=MapCategory.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False,
        label="سرگروه"
    )

    class Meta:
        model = MapCategory
        fields = ['name', 'parent_category']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'نام دسته بندی را وارد کنید'}),
            'parent_category': forms.Select(attrs={'class': 'form-control', 'blank': True}),
        }
        labels = {
            'name': 'نام دسته بندی',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['parent_category'].label_from_instance = lambda obj: obj.get_full_category_name()




class SearchForm(forms.Form):
    query = forms.CharField(
        label='متن جستجو', 
        max_length=100, 
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'جستجو...'})
    )
    FILTER_CHOICES = [
        ('all', 'همه'),
        ('cars', 'خودروها'),
        ('issues', 'مشکلات'),
        ('solutions', 'راهکارها'),
        ('tags', 'تگ‌ها'),
    ]
    filter_option = forms.ChoiceField(
        label='فیلتر',
        choices=FILTER_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
