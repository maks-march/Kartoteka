# core/mixins.py
from django.db import models
from django.contrib.contenttypes.fields import GenericRelation
import threading
from .audit import AuditLog


class AuditManager:
    """Менеджер для работы с аудитом"""

    @staticmethod
    def _get_client_ip(request):
        """Получение IP адреса клиента"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')

    @staticmethod
    def _model_to_dict(instance):
        """Преобразование модели в словарь для снимка"""
        from django.forms import model_to_dict
        data = model_to_dict(instance)
        # Преобразуем сложные типы в строки
        for key, value in data.items():
            if hasattr(value, 'pk'):
                data[key] = value.pk
            elif hasattr(value, '__str__'):
                data[key] = str(value)
        return data

    @classmethod
    def log_create(cls, request, instance):
        """Логирование создания объекта"""
        if not request:
            return

        AuditLog.objects.create(
            user=request.user if request.user.is_authenticated else None,
            user_ip=cls._get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            action='CREATE',
            content_type=instance.get_content_type(),
            object_id=instance.pk,
            object_repr=str(instance),
            changes={},
            snapshot=cls._model_to_dict(instance),
        )

    @classmethod
    def log_update(cls, request, instance, changes):
        """Логирование изменения объекта"""
        if not request:
            return

        AuditLog.objects.create(
            user=request.user if request.user.is_authenticated else None,
            user_ip=cls._get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            action='UPDATE',
            content_type=instance.get_content_type(),
            object_id=instance.pk,
            object_repr=str(instance),
            changes=changes,
            snapshot=cls._model_to_dict(instance),
        )

    @classmethod
    def log_delete(cls, request, instance):
        """Логирование удаления объекта"""
        if not request:
            return

        AuditLog.objects.create(
            user=request.user if request.user.is_authenticated else None,
            user_ip=cls._get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            action='DELETE',
            content_type=instance.get_content_type(),
            object_id=instance.pk,
            object_repr=str(instance),
            changes={},
            snapshot=cls._model_to_dict(instance),
        )

    @staticmethod
    def get_history(instance):
        """Получение истории изменений объекта"""
        return AuditLog.objects.filter(
            content_type=instance.get_content_type(),
            object_id=instance.pk,
        ).select_related('user').order_by('-timestamp')


class AuditableMixin(models.Model):
    """Миксин для добавления аудита в модель"""

    audit_logs = GenericRelation(AuditLog)

    class Meta:
        abstract = True

    def get_content_type(self):
        """Получение ContentType для модели"""
        from django.contrib.contenttypes.models import ContentType
        return ContentType.objects.get_for_model(self)

    def _get_current_request(self):
        """Получение текущего request (без импорта)"""
        return getattr(threading.current_thread(), 'current_request', None)

    def save(self, *args, **kwargs):
        """Переопределение save с отслеживанием изменений"""
        request = self._get_current_request()

        if not self.pk:
            # Новая запись
            super().save(*args, **kwargs)
            if request:
                AuditManager.log_create(request, self)
        else:
            # Существующая запись
            old = self.__class__.objects.get(pk=self.pk)
            changes = self._get_changes(old)

            super().save(*args, **kwargs)

            if changes and request:
                AuditManager.log_update(request, self, changes)

    def delete(self, *args, **kwargs):
        """Переопределение delete с логированием"""
        request = self._get_current_request()
        if request:
            AuditManager.log_delete(request, self)
        super().delete(*args, **kwargs)

    def _get_changes(self, old):
        """Получение списка измененных полей"""
        changes = {}
        for field in self._meta.fields:
            if field.primary_key:
                continue

            old_value = getattr(old, field.name)
            new_value = getattr(self, field.name)

            if old_value != new_value:
                changes[field.name] = {
                    'old': str(old_value) if old_value is not None else None,
                    'new': str(new_value) if new_value is not None else None,
                }
        return changes