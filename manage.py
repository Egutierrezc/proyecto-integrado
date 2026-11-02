#!/usr/bin/env python
"""Comando para ejecutar tareas administrativas de Django."""
import os
import sys


def main():
    """Ejecuta el comando de Django indicado en la terminal."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "No se pudo importar Django. Comprueba que esté instalado y "
            "disponible en PYTHONPATH, y que hayas activado el entorno virtual."
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
