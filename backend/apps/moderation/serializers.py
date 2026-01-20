"""
Serializers для moderation приложения
"""
from rest_framework import serializers
from .models import Complaint, Ban
from apps.accounts.serializers import UserSerializer
from apps.activities.serializers import RequestSerializer


class ComplaintSerializer(serializers.ModelSerializer):
    complainant = UserSerializer(read_only=True)
    reported_user = UserSerializer(read_only=True)
    reported_request = RequestSerializer(read_only=True)
    moderator = UserSerializer(read_only=True)
    
    class Meta:
        model = Complaint
        fields = ['id', 'complainant', 'reported_user', 'reported_request',
                 'complaint_type', 'description', 'status', 'moderator',
                 'moderator_comment', 'created_at', 'updated_at']
        read_only_fields = ['id', 'complainant', 'moderator', 'created_at', 'updated_at']


class BanSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    moderator = UserSerializer(read_only=True)
    
    class Meta:
        model = Ban
        fields = ['id', 'user', 'ban_type', 'reason', 'moderator',
                 'starts_at', 'ends_at', 'is_active', 'created_at']
        read_only_fields = ['id', 'moderator', 'created_at']
