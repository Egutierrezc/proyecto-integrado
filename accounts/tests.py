from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase, override_settings


class AuthenticationFlowTests(TestCase):
    def test_login_page_has_branded_form(self):
        response = self.client.get('/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Inicia sesión en tu cuenta')
        self.assertContains(response, 'csrfmiddlewaretoken')
        self.assertContains(response, '<button class="button button-secondary" type="button" disabled>Crear una cuenta</button>', html=True)

    def test_dashboard_requires_login_and_login_succeeds(self):
        User.objects.create_user(
            username='persona',
            email='persona@empresa.com',
            password='UnaClaveLarga!2026',
        )

        self.assertRedirects(self.client.get('/panel/'), '/?next=/panel/')

        response = self.client.post(
            '/',
            {'username': 'PERSONA@empresa.com', 'password': 'UnaClaveLarga!2026'},
        )
        self.assertRedirects(response, '/panel/')
        self.assertContains(self.client.get('/panel/'), 'Has iniciado sesión correctamente.')

    def test_login_rejects_email_and_password_over_twenty_characters(self):
        response = self.client.post(
            '/',
            {
                'username': 'persona@empresa-larga.com',
                'password': 'UnaClaveDeMasDe20Caracteres',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('username', response.context['form'].errors)
        self.assertIn('password', response.context['form'].errors)
        self.assertContains(response, 'maxlength="20"', count=2)

    def test_password_reset_page_renders(self):
        response = self.client.get('/recuperar-contrasena/')

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/password_reset.html')
        self.assertContains(response, '¿Olvidaste tu contraseña?')
        self.assertContains(response, 'Volver a estar al día')
        self.assertContains(response, 'Volver al inicio')
        self.assertContains(response, 'No te preocupes. Ingresa tu correo y te enviaremos las instrucciones.')

    def test_password_reset_status_pages_share_one_template(self):
        responses = (
            self.client.get('/recuperar-contrasena/enviado/'),
            self.client.get('/restablecer/invalid/invalid-token/'),
            self.client.get('/restablecer/listo/'),
        )

        for response in responses:
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, 'accounts/password_reset.html')

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_password_reset_sends_recovery_link(self):
        User.objects.create_user(
            username='persona',
            email='persona@empresa.com',
            password='UnaClaveLarga!2026',
        )

        response = self.client.post(
            '/recuperar-contrasena/',
            {'email': 'persona@empresa.com'},
        )

        self.assertRedirects(response, '/recuperar-contrasena/enviado/')
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('/restablecer/', mail.outbox[0].body)
