from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = 'Картотека промышленных объектов'

    def ready(self):
        """
        Метод вызывается при запуске приложения.
        Здесь можно импортировать сигналы или выполнить другую инициализацию.
        """
        # Импортируем сигналы, если они есть
        # import core.signals
        pass
