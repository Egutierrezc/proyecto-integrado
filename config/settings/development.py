"""Ajustes locales para ejecutar y probar el proyecto."""

import os

from django.core.management.utils import get_random_secret_key

from .base import *

DEBUG = True
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY') or get_random_secret_key()
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '[::1]']
