def user_id(request):
    # اگر کاربر وارد سیستم شده باشد، شناسه آن را برمی‌گرداند
    if request.user.is_authenticated:
        return {'user_id': request.user.id}
    return {'user_id': None}