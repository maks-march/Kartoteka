# core/middleware.py
import threading


class AuditMiddleware:
    """Middleware для передачи request в модели"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Сохраняем request в текущем потоке
        threading.current_thread().current_request = request
        try:
            response = self.get_response(request)
        finally:
            # Очищаем после обработки
            threading.current_thread().current_request = None
        return response
