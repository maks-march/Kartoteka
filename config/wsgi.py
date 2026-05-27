"""
WSGI config for project.
"""
import os
import sys
from django.core.wsgi import get_wsgi_application


path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if path not in sys.path:
    sys.path.append(path)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')


print(f"🚀 WSGI application starting...")
print(f"📁 Project path: {path}")
print(f"📁 Settings: {os.environ['DJANGO_SETTINGS_MODULE']}")

application = get_wsgi_application()