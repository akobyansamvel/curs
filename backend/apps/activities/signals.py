"""
Сигналы для activities приложения
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Review
from apps.accounts.models import Profile
from django.db.models import Avg
from decimal import Decimal


def recalculate_user_rating(user):
    """Пересчитывает рейтинг пользователя на основе всех отзывов"""
    try:
        profile = user.profile
    except AttributeError:
        # Если профиля нет, создаем его
        all_reviews = Review.objects.filter(reviewed_user=user)
        if all_reviews.exists():
            avg_rating = all_reviews.aggregate(avg=Avg('rating'))['avg']
            rating_value = Decimal(str(round(avg_rating, 2)))
        else:
            rating_value = Decimal('0.00')
        Profile.objects.create(user=user, rating=rating_value)
        return
    
    # Пересчитываем средний рейтинг из всех отзывов
    all_reviews = Review.objects.filter(reviewed_user=user)
    if all_reviews.exists():
        avg_rating = all_reviews.aggregate(avg=Avg('rating'))['avg']
        # Округляем до 2 знаков после запятой
        profile.rating = Decimal(str(round(avg_rating, 2)))
    else:
        # Если отзывов нет, рейтинг = 0
        profile.rating = Decimal('0.00')
    profile.save()


@receiver(post_save, sender=Review)
def review_saved(sender, instance, created, **kwargs):
    """Пересчитывает рейтинг при создании или изменении отзыва"""
    recalculate_user_rating(instance.reviewed_user)


@receiver(post_delete, sender=Review)
def review_deleted(sender, instance, **kwargs):
    """Пересчитывает рейтинг при удалении отзыва"""
    recalculate_user_rating(instance.reviewed_user)
