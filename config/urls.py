"""Rutas principales del panel de administración y de la aplicación."""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('accounts.urls')),
    path('home/', include('home.urls')),
]
