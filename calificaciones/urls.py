from django.urls import path

from . import views


urlpatterns = [
    path('', views.mantenedor, name='calificaciones'),
    path('calcular/', views.calcular_factores, name='calcular_factores'),
    path('ingresar/', views.ingresar_calificacion, name='ingresar_calificacion'),
]
