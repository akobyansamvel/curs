"""
Serializers для accounts приложения
"""
from rest_framework import serializers
from .models import User, Profile, Interest


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 
                 'telegram_id', 'telegram_verified', 'phone_verified', 
                 'is_moderator', 'date_joined']
        read_only_fields = ['id', 'date_joined']


class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    rating = serializers.DecimalField(max_digits=3, decimal_places=2, coerce_to_string=False, default=0.00)
    available_schedule = serializers.JSONField(required=False, allow_null=True)
    
    class Meta:
        model = Profile
        fields = ['id', 'user', 'photo', 'city', 'rating', 'bio', 
                 'available_schedule', 'created_at', 'updated_at']
        read_only_fields = ['id', 'rating', 'created_at', 'updated_at']
    
    def to_internal_value(self, data):
        """Обрабатывает available_schedule если пришёл как JSON строка"""
        import json
        
        if isinstance(data, dict):
            data = data.copy()
        elif hasattr(data, 'copy'):
            data = data.copy()
        elif hasattr(data, 'dict'):
            data = data.dict()
        else:
            data = dict(data) if data else {}
        
        if 'available_schedule' in data:
            value = data['available_schedule']
            if isinstance(value, str):
                try:
                    parsed = json.loads(value)
                    data['available_schedule'] = parsed if isinstance(parsed, dict) else {}
                except (json.JSONDecodeError, ValueError, TypeError):
                    data['available_schedule'] = {}
            elif value is None or value == '':
                data['available_schedule'] = {}
            elif not isinstance(value, dict):
                data['available_schedule'] = {}
        
        return super().to_internal_value(data)
    
    def to_representation(self, instance):
        """Убеждаемся, что rating всегда число и фото имеет полный URL"""
        data = super().to_representation(instance)
        # Убеждаемся, что rating всегда число, даже если None
        rating_value = data.get('rating')
        if rating_value is None:
            data['rating'] = 0.0
        else:
            # Преобразуем Decimal в float для JSON
            try:
                data['rating'] = float(rating_value)
            except (ValueError, TypeError):
                data['rating'] = 0.0
        # Убеждаемся, что все числовые поля корректны
        if 'available_schedule' not in data or data['available_schedule'] is None:
            data['available_schedule'] = {}
        # Формируем полный URL для фото
        if instance.photo:
            request = self.context.get('request')
            if request:
                try:
                    data['photo'] = request.build_absolute_uri(instance.photo.url)
                except:
                    from django.conf import settings
                    data['photo'] = f"{request.build_absolute_uri('/')[:-1]}{settings.MEDIA_URL}{instance.photo.name}"
            else:
                from django.conf import settings
                data['photo'] = f"{settings.MEDIA_URL}{instance.photo.name}"
        return data


class InterestSerializer(serializers.ModelSerializer):
    activity_id = serializers.IntegerField(write_only=True, required=False)
    
    class Meta:
        model = Interest
        fields = ['id', 'activity', 'activity_id', 'level', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Lazy import to avoid circular dependency
        from apps.activities.serializers import ActivitySerializer
        self.fields['activity'] = ActivitySerializer(read_only=True)
