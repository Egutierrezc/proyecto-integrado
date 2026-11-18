from django.contrib import admin
from .models import (
    Corredor,
    Mercado,
    Usuario,
    Calificacion,
    Factor,
    Log
)

admin.site.register(Corredor)
admin.site.register(Mercado)
admin.site.register(Usuario)
admin.site.register(Calificacion)
admin.site.register(Factor)
admin.site.register(Log)


