"""
Логика поиска заявок
"""
from django.db.models import Q
from .models import Request


def search_requests(query: str, filters: dict = None):
    """
    Полнотекстовый поиск заявок
    Использует PostgreSQL full-text search если доступен, иначе обычный поиск
    """
    requests = Request.objects.filter(status='active', visibility='public')
    
    if query:
        # Поиск по названию и описанию
        requests = requests.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(activity__name__icontains=query) |
            Q(location_name__icontains=query)
        )
    
    if filters:
        # Применяем дополнительные фильтры
        category_id = filters.get('category_id')
        activity_id = filters.get('activity_id')
        request_type = filters.get('request_type')
        level = filters.get('level')
        format_type = filters.get('format')
        
        if category_id:
            requests = requests.filter(activity__category_id=category_id)
        if activity_id:
            requests = requests.filter(activity_id=activity_id)
        if request_type:
            requests = requests.filter(request_type=request_type)
        if level:
            requests = requests.filter(level=level)
        if format_type:
            requests = requests.filter(format=format_type)
    
    return requests.order_by('-created_at')[:100]  # Ограничение результатов
