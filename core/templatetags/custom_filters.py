from django import template
import re


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