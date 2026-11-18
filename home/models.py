from django.conf import settings
from django.db import models


# Create your models here.
class Corredor(models.Model):
    nombre = models.CharField(max_length=150)
    rut = models.CharField(max_length=12, unique=True)

    def __str__(self):
        return self.nombre


class Mercado(models.Model):
    nombre = models.CharField(max_length=150)
    codigo = models.CharField(max_length=30, unique=True)

    def __str__(self):
        return self.nombre


class Usuario(models.Model):
    cuenta = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="perfil_tributario"
    )
    corredor = models.ForeignKey(
        Corredor,
        on_delete=models.PROTECT,
        related_name="usuarios"
    )
    rol = models.CharField(max_length=50)

    def __str__(self):
        return self.cuenta.get_username()


class Calificacion(models.Model):
    ejercicio = models.IntegerField()
    mercado = models.ForeignKey(
        Mercado,
        on_delete=models.PROTECT
    )
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT
    )
    corredor = models.ForeignKey(
        Corredor,
        on_delete=models.PROTECT
    )
    instrumento = models.CharField(max_length=100)
    fecha_pago = models.DateField()
    secuencia = models.IntegerField()
    dividendo = models.DecimalField(max_digits=15, decimal_places=2)
    tipo_sociedad = models.CharField(max_length=100)
    valor_historico = models.DecimalField(max_digits=15, decimal_places=2)
    origen = models.CharField(max_length=150)
    fuente_ingreso = models.CharField(max_length=150)
    factor_actualizacion = models.DecimalField(
        max_digits=12,
        decimal_places=6
    )
    descripcion = models.TextField(blank=True)

    def __str__(self):
        return f"Calificacion {self.id} - {self.instrumento}"


class Factor(models.Model):
    calificacion = models.ForeignKey(
        Calificacion,
        on_delete=models.CASCADE,
        related_name="factores"
    )
    numero_factor = models.IntegerField()
    monto = models.DecimalField(
        max_digits=15,
        decimal_places=2
    )
    valor_factor = models.DecimalField(
        max_digits=15,
        decimal_places=6
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["calificacion", "numero_factor"],
                name="factor_unico_por_calificacion"
            ),
            models.CheckConstraint(
                condition=models.Q(numero_factor__gte=8)
                & models.Q(numero_factor__lte=37),
                name="numero_factor_entre_8_y_37"
            ),
        ]

    def __str__(self):
        return f"Factor {self.numero_factor} - Calificacion {self.calificacion_id}"



class Log(models.Model):
    ACCIONES = [
        ("CREAR", "Creación"),
        ("MODIFICAR", "Modificación"),
        ("ELIMINAR", "Eliminación"),
    ]

    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name="logs"
    )
    calificacion = models.ForeignKey(
        Calificacion,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="logs"
    )
    accion = models.CharField(
        max_length=20,
        choices=ACCIONES
    )
    fecha_hora = models.DateTimeField(
        auto_now_add=True
    )
    detalle = models.TextField(blank=True)

    def __str__(self):
        return f"{self.accion} - {self.fecha_hora}"
