"""
Middleware для отключения CSRF проверки для API endpoints
"""
from django.utils.deprecation import MiddlewareMixin


class DisableCSRFForAPI(MiddlewareMixin):
    """
    Отключает CSRF проверку для всех запросов к API
    """
    def process_request(self, request):
        # Отключаем CSRF для всех путей, начинающихся с /api/
        if request.path.startswith('/api/'):
            setattr(request, '_dont_enforce_csrf_checks', True)
        return None
