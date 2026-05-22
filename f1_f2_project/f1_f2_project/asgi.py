import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'f1_f2_project.settings')


application = get_asgi_application()

print(f"🚀 ASGI application initialized for f1_f2_project")
print(f"📁 Settings module: {os.environ['DJANGO_SETTINGS_MODULE']}")