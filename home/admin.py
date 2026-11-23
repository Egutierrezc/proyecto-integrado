
from django.contrib import admin
from django.core.exceptions import PermissionDenied
from .models import Corredor, Mercado, Usuario, Calificacion, Factor, Log
from .auditoria import registrar_cambio


@admin.register(Calificacion)
class CalificacionAdmin(admin.ModelAdmin):

    def obtener_actor(self, request):
        actor = Usuario.objects.filter(
            cuenta=request.user
        ).first()

        if actor is None:
            raise PermissionDenied(
                "El usuario necesita un perfil tributario."
            )

        return actor

    
       
    def registrar_auditoria(self, actor, calificacion, accion):
        registrar_cambio(
            actor=actor,
            calificacion=calificacion,
            accion=accion,
            origen="ADMIN_DJANGO",
            forma_actualizacion="MANUAL",
            detalle=f"{accion} de calificacion ID {calificacion.pk}"
        )


    def save_model(self, request, obj, form, change):
        actor = self.obtener_actor(request)

        super().save_model(request, obj, form, change)

        accion = "MODIFICAR" if change else "CREAR"
        self.registrar_auditoria(actor, obj, accion)

    def delete_model(self, request, obj):
        actor = self.obtener_actor(request)
        self.registrar_auditoria(actor, obj, "ELIMINAR")

        super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        actor = self.obtener_actor(request)

        for obj in queryset:
            self.registrar_auditoria(actor, obj, "ELIMINAR")

        super().delete_queryset(request, queryset)


admin.site.register(Corredor)
admin.site.register(Mercado)
admin.site.register(Usuario)
admin.site.register(Factor)

@admin.register(Log)
class LogAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "usuario",
        "calificacion",
        "accion",
        "fecha_hora",
        "origen",
        "forma_actualizacion",
    )

    list_filter = (
        "accion",
        "origen",
        "forma_actualizacion",
    )

    readonly_fields = (
        "usuario",
        "calificacion",
        "accion",
        "fecha_hora",
        "detalle",
        "origen",
        "forma_actualizacion",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False



