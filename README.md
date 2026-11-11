# Tribu

Aplicación de gestión tributaria con Django 5.2 y Python 3.12.

## Ejecutar en Windows

Desde la carpeta del proyecto:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Abre http://127.0.0.1:8000/.

## Funciones

- Registro e inicio de sesión.
- Panel inicial.
- Recuperación de contraseña por correo.
- API de autenticación con token.

## API de token

- `POST /api/token/login/`: recibe `username` (nombre de usuario o correo) y `password`; devuelve un token.
- `GET /api/token/me/`: muestra el usuario autenticado.
- `POST /api/token/logout/`: invalida el token.

Envía el token en el encabezado `Authorization: Token <token>`. El login web también lo guarda en `localStorage` y `sessionStorage` como `authToken`; al cerrar sesión se elimina de ambos y de la base de datos. Django guarda las contraseñas con hash. Usa HTTPS en producción.

## Correo y producción

Para enviar correos con Gmail, configura `GMAIL_EMAIL` y `GMAIL_APP_PASSWORD` como variables de entorno. Usa una contraseña de aplicación, no la contraseña normal de Gmail.

En producción configura `DJANGO_SETTINGS_MODULE=config.settings.production`, `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`, `GMAIL_EMAIL` y `GMAIL_APP_PASSWORD`. Usa una clave secreta nueva, HTTPS y ejecuta `python manage.py collectstatic` durante el despliegue.
