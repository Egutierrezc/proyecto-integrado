# Tribu

Proyecto inicial de gestión tributaria construido con Django.

## Versiones

Python 3.12.10 y Django 5.2.x.

## Organización y configuración

- `accounts/` contiene la funcionalidad de cuentas y su presentación: vistas, formularios, rutas, pruebas, plantillas y archivos estáticos.
- `config/settings/base.py` comparte los ajustes entre entornos.
- `config/settings/development.py` configura el servidor local.
- `config/settings/production.py` exige secretos y activa protecciones HTTPS.

La arquitectura sigue las convenciones de Django (MVT), que corresponden a MVC así:

- **Modelo:** modelos de Django. La autenticación usa el modelo `User` incluido en Django.
- **Controlador:** `accounts/views.py` recibe las solicitudes y coordina las respuestas; `accounts/urls.py` dirige cada URL.
- **Vista:** plantillas HTML en `accounts/templates/accounts/`; sus estilos están en `accounts/static/accounts/`.

En Django, las funciones de `views.py` son el equivalente a los controladores de MVC; no hace falta crear una capa de callbacks aparte.

El servidor local usa `config.settings.development`. WSGI y ASGI usan `config.settings.production`; antes de desplegar, configura todas las variables requeridas para ese entorno. La clave anterior que estaba escrita en el código fue retirada: genera una clave nueva y no reutilices una que haya sido publicada.

El proyecto está organizado por funcionalidades Django: cada área nueva debe vivir en su propia aplicación e incluir sus rutas, vistas, formularios, modelos y pruebas. La base actual es SQLite para desarrollo; antes de atender varios usuarios en producción, configura una base de datos de servidor, como PostgreSQL, y un sistema de copias de seguridad.

## Iniciar en Windows

Desde esta carpeta, instala las dependencias y ejecuta el servidor:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py runserver
```

Abre `http://127.0.0.1:8000/`. Si necesitas crear la base de datos de nuevo:

```powershell
python manage.py migrate
```

## Envío de recuperación por Gmail

Django envía los correos mediante SMTP de Gmail. Necesitas activar la verificación en dos pasos en tu cuenta de Google y crear una **contraseña de aplicación**; no uses la contraseña normal de Gmail. Luego, en la misma ventana de PowerShell donde iniciarás el servidor, configura las variables:

```powershell
$env:GMAIL_EMAIL = "tu-cuenta@gmail.com"
$env:GMAIL_APP_PASSWORD = "tu contraseña de aplicación"
.\.venv\Scripts\python.exe manage.py runserver
```

No guardes la contraseña de aplicación en el código ni la compartas. Las variables solo estarán disponibles en esa ventana de PowerShell. Al solicitar el restablecimiento, Django enviará un mensaje únicamente si existe una cuenta asociada al correo ingresado. En desarrollo, el enlace recibido apunta a `127.0.0.1` y solo funcionará en tu equipo; en producción, configura un dominio público y HTTPS para que el usuario pueda abrirlo.

## Variables obligatorias en producción

Genera una clave secreta nueva con:

```powershell
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Configura las variables en el servicio de despliegue, no en el código. `DJANGO_ALLOWED_HOSTS` acepta dominios separados por comas:

```text
DJANGO_SETTINGS_MODULE=config.settings.production
DJANGO_SECRET_KEY=<clave nueva generada>
DJANGO_ALLOWED_HOSTS=<tu-dominio>
GMAIL_EMAIL=<cuenta remitente>
GMAIL_APP_PASSWORD=<contraseña de aplicación>
```

Usa HTTPS en el dominio configurado: producción redirige el tráfico a HTTPS y marca las cookies como seguras. Recopila los archivos estáticos durante el despliegue con `python manage.py collectstatic`.

La aplicación incluye inicio de sesión con correo y contraseña, recuperación de contraseña y un panel privado inicial. Las pantallas de recuperación comparten una sola plantilla HTML; el correo y su asunto usan plantillas independientes porque generan contenido de email. El botón de creación de cuenta aparece deshabilitado hasta que se implemente el registro.
