import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cosmetica.settings')

application = get_wsgi_application()

# Vercel expects the callable named 'app'
app = application
