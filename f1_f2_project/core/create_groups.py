from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from .models import Object, Participant, AutomatedSystem, Project, VendorProduct


class Command(BaseCommand):
    help = 'Создание групп пользователей и прав доступа'

    def handle(self, *args, **options):
        self.stdout.write('  Создание групп пользователей...')

        # Создаём группы
        admin_group, _ = Group.objects.get_or_create(name='Администраторы')
        editor_group, _ = Group.objects.get_or_create(name='Редакторы')
        viewer_group, _ = Group.objects.get_or_create(name='Просмотрщики')

        # Очищаем старые права
        editor_group.permissions.clear()
        viewer_group.permissions.clear()

        # Модели для которых настраиваем права
        models = [Object, Participant, AutomatedSystem, Project, VendorProduct]

        for model in models:
            ct = ContentType.objects.get_for_model(model)

            # Права для редакторов (добавление + изменение)
            add_perm = Permission.objects.get(
                content_type=ct,
                codename=f'add_{model._meta.model_name}'
            )
            change_perm = Permission.objects.get(
                content_type=ct,
                codename=f'change_{model._meta.model_name}'
            )
            editor_group.permissions.add(add_perm, change_perm)

            # Права для просмотрщиков (только просмотр)
            view_perm = Permission.objects.get(
                content_type=ct,
                codename=f'view_{model._meta.model_name}'
            )
            viewer_group.permissions.add(view_perm)

            self.stdout.write(f'    {model.__name__} настроен')

        self.stdout.write(self.style.SUCCESS('  Группы успешно созданы!'))