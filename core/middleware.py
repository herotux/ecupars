import threading
from django.utils.deprecation import MiddlewareMixin
from django.shortcuts import redirect





_thread_locals = threading.local()

def get_current_user():
    return getattr(_thread_locals, 'user', None)

class CurrentUserMiddleware(MiddlewareMixin):
    def process_request(self, request):
        _thread_locals.user = request.user

    def process_response(self, request, response):
        _thread_locals.user = None
        return response
    





class SessionExpiryMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if not request.user.is_authenticated:
            if request.path != '/login/':
                return redirect(f'/login/?next={request.path}')