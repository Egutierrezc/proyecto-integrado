
from .models import Log


def registrar_cambio(
    actor,
    calificacion,
    accion,
    origen,
    forma_actualizacion,
    detalle=""
):
    acciones_validas = ["CREAR", "MODIFICAR", "ELIMINAR"]
    formas_validas = ["MANUAL", "CARGA"]

    if accion not in acciones_validas:
        raise ValueError("Accion no valida")

    if forma_actualizacion not in formas_validas:
        raise ValueError("Forma de actualizacion no valida")

    if not origen:
        raise ValueError("El origen es obligatorio")

    return Log.objects.create(
        usuario=actor,
        calificacion=calificacion,
        accion=accion,
        origen=origen,
        forma_actualizacion=forma_actualizacion,
        detalle=detalle
    )

