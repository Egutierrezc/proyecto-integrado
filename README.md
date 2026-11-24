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

## Calificaciones tributarias (lógica inicial)

El cálculo automático aplica a los factores 8–33 a partir de montos homologados;
el denominador suma los montos 8–19. Se redondean a 8 decimales, no pueden
superar 1 y su suma de 8–19 no puede superar 1. Si el denominador es cero, se
informa el error y no se generan factores. La plantilla de carga contempla los
factores 8–37 (30 columnas); 34–37 son valores manuales sin fórmula homologada.
El factor 19B se ingresa manualmente en pantalla y queda fuera del CSV. El
mantenedor permite ingresar calificaciones manualmente, calcular factores desde
montos homologados en el servidor y guardar los registros asociados al corredor.
La edición, eliminación y cargas masivas siguen pendientes.

### Decisión de formulario para el cálculo de montos

El cálculo automático se limita al **Certificado 70 / 1948**, usando la
homologación de la hoja `3.2 Homologacion columnas`: factores 8–33 y montos
8–19 como denominador. La sección de **Certificado 44 / 1922** es una
homologación distinta y no se procesa con esa fórmula. La referencia a **DJ1949**
en `3.TIpos de datos` no queda vinculada de forma inequívoca a estas columnas;
por tanto, no se calcula automáticamente hasta confirmar su correspondencia.
Los montos sin homologación aplicable deben mantenerse en ingreso manual.

La identidad de una calificación se define por mercado, ejercicio, instrumento,
fecha de pago y secuencia del evento. El sistema admite una calificación de
origen sistema y una calificación local por corredor para la misma identidad;
el corredor ve su versión local en lugar de la del sistema, sin modificarla.
También están definidos los modelos de auditoría para conservar la identidad
del evento, el actor, el origen, el método de ingreso y los cambios.

## API de token

- `POST /api/token/login/`: recibe `username` (nombre de usuario o correo) y `password`; devuelve un token.
- `GET /api/token/me/`: muestra el usuario autenticado.
- `POST /api/token/logout/`: invalida el token.

Envía el token en el encabezado `Authorization: Token <token>`. El login web también lo guarda en `localStorage` y `sessionStorage` como `authToken`; al cerrar sesión se elimina de ambos y de la base de datos. Django guarda las contraseñas con hash. Usa HTTPS en producción.

## Correo y producción

Para enviar correos con Gmail, configura `GMAIL_EMAIL` y `GMAIL_APP_PASSWORD` como variables de entorno. Usa una contraseña de aplicación, no la contraseña normal de Gmail.

En producción configura `DJANGO_SETTINGS_MODULE=config.settings.production`, `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`, `GMAIL_EMAIL` y `GMAIL_APP_PASSWORD`. Usa una clave secreta nueva, HTTPS y ejecuta `python manage.py collectstatic` durante el despliegue.
