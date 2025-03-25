from django import template
import re
from django.contrib.humanize.templatetags.humanize import intcomma

register = template.Library()

@register.filter(name='add_class')
def add_class(field, css_class):
    return field.as_widget(attrs={"class": css_class})




@register.filter
def convert_tags(input_string):
    if not input_string:
        return ''
    # حذف براکت‌ها و نماد <Tag: >
    cleaned_string = re.sub(r'\[|\]|<Tag: |>', '', input_string)
    # تقسیم رشته بر اساس کاما و حذف فضاهای اضافی
    tags_list = [tag.strip() for tag in cleaned_string.split(',')]
    # تبدیل لیست به رشته با کاما و فاصله
    result = ', '.join(tags_list)
    return result





@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)





def to_persian_numbers(value):
    persian_numbers = {
        '0': '۰',
        '1': '۱',
        '2': '۲',
        '3': '۳',
        '4': '۴',
        '5': '۵',
        '6': '۶',
        '7': '۷',
        '8': '۸',
        '9': '۹',
        ',': '،',  # تبدیل کاما به ممیز فارسی (اختیاری)
    }
    return ''.join(persian_numbers.get(c, c) for c in str(value))

@register.filter
def toman_format(value):
    value = int(value)  # حذف اعشار اگر وجود دارد
    formatted = intcomma(value)  # جدا کردن سه‌رقمی
    return to_persian_numbers(formatted)