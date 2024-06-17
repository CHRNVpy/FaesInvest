"""
WSGI config for invest project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application
from whitenoise import WhiteNoise

from invest.invest.settings import BASE_DIR

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'invest.settings')

application = get_wsgi_application()

application = WhiteNoise(application, root=os.path.join(BASE_DIR, 'static'))
