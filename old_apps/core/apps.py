from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    verbose_name = 'Картотека промышленных объектов'
    name = 'old_apps.core'
    label = 'core'
    def ready(self):
        """
        Метод вызывается при запуске приложения.
        Здесь можно импортировать сигналы или выполнить другую инициализацию.
        """
        # Импортируем сигналы, если они есть
        # import core.signals
        pass
