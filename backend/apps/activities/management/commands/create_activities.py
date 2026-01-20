"""
Команда для создания категорий и активностей в базе данных
"""
from django.core.management.base import BaseCommand
from apps.activities.models import Category, Activity


class Command(BaseCommand):
    help = 'Создаёт категории и активности в базе данных'

    def handle(self, *args, **options):
        # Категории и активности
        activities_data = [
            {
                'category': {
                    'name': 'Спорт',
                    'slug': 'sport',
                    'icon': '🏃'
                },
                'activities': [
                    {'name': 'Футбол', 'slug': 'football', 'description': 'Игра в футбол на поле', 'icon': '⚽'},
                    {'name': 'Баскетбол', 'slug': 'basketball', 'description': 'Игра в баскетбол', 'icon': '🏀'},
                    {'name': 'Волейбол', 'slug': 'volleyball', 'description': 'Игра в волейбол', 'icon': '🏐'},
                    {'name': 'Теннис', 'slug': 'tennis', 'description': 'Большой теннис', 'icon': '🎾'},
                    {'name': 'Бег', 'slug': 'running', 'description': 'Бег трусцой, марафон', 'icon': '🏃'},
                    {'name': 'Велоспорт', 'slug': 'cycling', 'description': 'Велосипедные прогулки и тренировки', 'icon': '🚴'},
                    {'name': 'Плавание', 'slug': 'swimming', 'description': 'Плавание в бассейне или открытой воде', 'icon': '🏊'},
                    {'name': 'Йога', 'slug': 'yoga', 'description': 'Йога и растяжка', 'icon': '🧘'},
                    {'name': 'Тренажёрный зал', 'slug': 'gym', 'description': 'Тренировки в зале', 'icon': '💪'},
                    {'name': 'Бокс', 'slug': 'boxing', 'description': 'Бокс и единоборства', 'icon': '🥊'},
                ]
            },
            {
                'category': {
                    'name': 'Развлечения',
                    'slug': 'entertainment',
                    'icon': '🎮'
                },
                'activities': [
                    {'name': 'Настольные игры', 'slug': 'board-games', 'description': 'Играем в настольные игры', 'icon': '🎲'},
                    {'name': 'Кино', 'slug': 'cinema', 'description': 'Поход в кинотеатр', 'icon': '🎬'},
                    {'name': 'Концерт', 'slug': 'concert', 'description': 'Посещение концертов', 'icon': '🎵'},
                    {'name': 'Театр', 'slug': 'theater', 'description': 'Поход в театр', 'icon': '🎭'},
                    {'name': 'Квесты', 'slug': 'quests', 'description': 'Квест-комнаты и квесты', 'icon': '🔍'},
                    {'name': 'Боулинг', 'slug': 'bowling', 'description': 'Игра в боулинг', 'icon': '🎳'},
                    {'name': 'Бильярд', 'slug': 'billiards', 'description': 'Игра в бильярд', 'icon': '🎱'},
                    {'name': 'Настольный теннис', 'slug': 'table-tennis', 'description': 'Пинг-понг', 'icon': '🏓'},
                    {'name': 'Виртуальная реальность', 'slug': 'vr', 'description': 'VR-развлечения', 'icon': '🥽'},
                    {'name': 'Караоке', 'slug': 'karaoke', 'description': 'Пение в караоке', 'icon': '🎤'},
                ]
            },
            {
                'category': {
                    'name': 'Активный отдых',
                    'slug': 'active-recreation',
                    'icon': '🏔️'
                },
                'activities': [
                    {'name': 'Походы', 'slug': 'hiking', 'description': 'Пешие походы', 'icon': '🥾'},
                    {'name': 'Скалолазание', 'slug': 'climbing', 'description': 'Скалолазание и альпинизм', 'icon': '🧗'},
                    {'name': 'Рыбалка', 'slug': 'fishing', 'description': 'Рыбалка', 'icon': '🎣'},
                    {'name': 'Кемпинг', 'slug': 'camping', 'description': 'Кемпинг и отдых на природе', 'icon': '⛺'},
                    {'name': 'Катание на лыжах', 'slug': 'skiing', 'description': 'Горные и беговые лыжи', 'icon': '⛷️'},
                    {'name': 'Сноуборд', 'slug': 'snowboarding', 'description': 'Катание на сноуборде', 'icon': '🏂'},
                    {'name': 'Сёрфинг', 'slug': 'surfing', 'description': 'Сёрфинг и виндсёрфинг', 'icon': '🏄'},
                    {'name': 'Дайвинг', 'slug': 'diving', 'description': 'Подводное плавание', 'icon': '🤿'},
                    {'name': 'Каякинг', 'slug': 'kayaking', 'description': 'Сплав на байдарках и каяках', 'icon': '🛶'},
                    {'name': 'Велосипедные прогулки', 'slug': 'bike-tours', 'description': 'Велотуры и прогулки', 'icon': '🚵'},
                ]
            },
            {
                'category': {
                    'name': 'Танцы',
                    'slug': 'dancing',
                    'icon': '💃'
                },
                'activities': [
                    {'name': 'Латиноамериканские танцы', 'slug': 'latin', 'description': 'Сальса, бачата, ча-ча-ча', 'icon': '💃'},
                    {'name': 'Бальные танцы', 'slug': 'ballroom', 'description': 'Бальные танцы', 'icon': '🕺'},
                    {'name': 'Хип-хоп', 'slug': 'hip-hop', 'description': 'Хип-хоп танцы', 'icon': '🎵'},
                    {'name': 'Современные танцы', 'slug': 'contemporary', 'description': 'Современная хореография', 'icon': '🎭'},
                    {'name': 'Балет', 'slug': 'ballet', 'description': 'Классический балет', 'icon': '🩰'},
                ]
            },
        ]

        created_categories = 0
        created_activities = 0

        for category_data in activities_data:
            category, created = Category.objects.get_or_create(
                slug=category_data['category']['slug'],
                defaults={
                    'name': category_data['category']['name'],
                    'icon': category_data['category']['icon']
                }
            )
            
            if created:
                created_categories += 1
                self.stdout.write(
                    self.style.SUCCESS(f'[OK] Создана категория: {category.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'[SKIP] Категория уже существует: {category.name}')
                )

            for activity_data in category_data['activities']:
                activity, created = Activity.objects.get_or_create(
                    slug=activity_data['slug'],
                    defaults={
                        'name': activity_data['name'],
                        'category': category,
                        'description': activity_data['description'],
                        'icon': activity_data['icon'],
                        'is_active': True
                    }
                )
                
                if created:
                    created_activities += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'  [OK] Создана активность: {activity.name}')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'  [SKIP] Активность уже существует: {activity.name}')
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nГотово! Создано категорий: {created_categories}, активностей: {created_activities}'
            )
        )
