#!/usr/bin/env python
"""Заполнение базы тестовыми данными."""
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.contrib.auth import get_user_model
from core.models import Category, Object

User = get_user_model()

# Создаём суперпользователя
if not User.objects.filter(username="admin").exists():
    User.objects.create_superuser("admin", "admin@example.com", "admin")
    print("✅ Суперпользователь создан: admin / admin")

# Категории
categories_data = [
    {"name": "Оружие", "level": 1},
    {"name": "Броня", "level": 2},
    {"name": "Зелья", "level": 3},
    {"name": "Архитектура", "level": 1},
    {"name": "Магия", "level": 2},
]

cats = {}
for cd in categories_data:
    cat, created = Category.objects.get_or_create(name=cd["name"], defaults={"level": cd["level"]})
    cats[cd["name"]] = cat
    print(f"{'Создана' if created else 'Найдена'} категория: {cat}")

# Объекты
objects_data = [
    {"name": "Меч", "level": 1, "category": "Оружие"},
    {"name": "Лук", "level": 1, "category": "Оружие"},
    {"name": "Щит", "level": 1, "category": "Броня"},
    {"name": "Кираса", "level": 2, "category": "Броня"},
    {"name": "Зелье здоровья", "level": 1, "category": "Зелья"},
    {"name": "Зелье маны", "level": 2, "category": "Зелья"},
    {"name": "Замок", "level": 3, "category": "Архитектура"},
    {"name": "Башня", "level": 1, "category": "Архитектура"},
    {"name": "Огненный шар", "level": 1, "category": "Магия"},
    {"name": "Ледяная стрела", "level": 2, "category": "Магия"},
]

for od in objects_data:
    obj, created = Object.objects.get_or_create(
        name=od["name"],
        defaults={"level": od["level"], "category": cats[od["category"]]},
    )
    print(f"{'Создан' if created else 'Найден'} объект: {obj}")

print("\n✅ Тестовые данные загружены!")
