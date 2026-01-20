from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, Profile


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Автоматически создавать профиль при создании пользователя"""
    if created:
        from decimal import Decimal
        Profile.objects.create(user=instance, rating=Decimal('0.00'))
