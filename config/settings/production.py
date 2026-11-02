"""Ajustes seguros para publicar el proyecto."""

import os

from django.core.exceptions import ImproperlyConfigured

from .base import *


def required_setting(name):
    value = os.environ.get(name, '').strip()
    if not value:
        raise ImproperlyConfigured(f'Falta la variable de entorno obligatoria: {name}')
    return value


SECRET_KEY = required_setting('DJANGO_SECRET_KEY')
ALLOWED_HOSTS = [
    host.strip()
    for host in required_setting('DJANGO_ALLOWED_HOSTS').split(',')
    if host.strip()
]
if not ALLOWED_HOSTS:
    raise ImproperlyConfigured('DJANGO_ALLOWED_HOSTS debe incluir al menos un dominio.')

EMAIL_HOST_USER = required_setting('GMAIL_EMAIL')
EMAIL_HOST_PASSWORD = required_setting('GMAIL_APP_PASSWORD')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', EMAIL_HOST_USER)

DEBUG = False
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31_536_000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
