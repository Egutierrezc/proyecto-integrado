from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase, override_settings
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase


class AuthenticationFlowTests(TestCase):
    def test_login_page_has_branded_form(self):
        response = self.client.get('/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Inicia sesión en tu cuenta')
        self.assertContains(response, 'csrfmiddlewaretoken')
        self.assertContains(response, '<a class="button button-secondary" href="/registro/">Crear una cuenta</a>', html=True)

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

    def test_web_login_stores_api_token_in_browser_storage_and_logout_revokes_it(self):
        user = User.objects.create_user(
            username='token-persona',
            email='token-persona@empresa.com',
            password='UnaClaveLarga!2026',
        )

        self.client.post(
            '/',
            {'username': 'TOKEN-PERSONA@EMPRESA.COM', 'password': 'UnaClaveLarga!2026'},
        )
        response = self.client.get('/panel/')

        self.assertEqual(response.status_code, 200)
        token = Token.objects.get(user=user)
        self.assertContains(response, token.key)
        self.assertContains(response, "localStorage.setItem('authToken', apiToken)")
        self.assertContains(response, "sessionStorage.setItem('authToken', apiToken)")
        self.assertContains(response, "localStorage.removeItem('authToken')")
        self.assertContains(response, "sessionStorage.removeItem('authToken')")

        response = self.client.post('/cerrar-sesion/')

        self.assertRedirects(response, '/')
        self.assertFalse(Token.objects.filter(user=user).exists())

    def test_login_rejects_email_over_fifty_and_password_over_twenty_characters(self):
        response = self.client.post(
            '/',
            {
                'username': f"persona@{'a' * 45}.com",
                'password': 'UnaClaveDeMasDe20Caracteres',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('username', response.context['form'].errors)
        self.assertIn('password', response.context['form'].errors)
        self.assertContains(response, 'maxlength="50"', count=1)
        self.assertContains(response, 'maxlength="20"', count=1)

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


class TokenAuthenticationApiTests(APITestCase):
    def setUp(self):
        self.username = 'api-persona'
        self.password = 'UnaClaveLarga!2026'
        self.user = User.objects.create_user(
            username=self.username,
            email='api-persona@empresa.com',
            password=self.password,
        )

    def test_login_returns_persisted_token_and_password_is_hashed(self):
        response = self.client.post(
            '/api/token/login/',
            {'username': self.username, 'password': self.password},
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        token = Token.objects.get(user=self.user)
        self.assertEqual(response.data['token'], token.key)
        self.assertNotEqual(self.user.password, self.password)
        self.assertTrue(self.user.check_password(self.password))

    def test_login_accepts_email_and_rejects_invalid_password(self):
        response = self.client.post(
            '/api/token/login/',
            {'username': 'API-PERSONA@EMPRESA.COM', 'password': self.password},
            format='json',
        )
        self.assertEqual(response.status_code, 200)

        Token.objects.filter(user=self.user).delete()
        response = self.client.post(
            '/api/token/login/',
            {'username': self.username, 'password': 'incorrecta'},
            format='json',
        )

        self.assertEqual(response.status_code, 401)
        self.assertFalse(Token.objects.filter(user=self.user).exists())

    def test_login_reuses_existing_token(self):
        old_token = Token.objects.create(user=self.user)

        response = self.client.post(
            '/api/token/login/',
            {'username': self.username, 'password': self.password},
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['token'], old_token.key)
        self.assertEqual(Token.objects.filter(user=self.user).count(), 1)

    def test_logout_deletes_token_and_invalidates_authenticated_requests(self):
        token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

        self.assertEqual(self.client.get('/api/token/me/').status_code, 200)
        response = self.client.post('/api/token/logout/', format='json')

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Token.objects.filter(user=self.user).exists())
        self.assertEqual(self.client.get('/api/token/me/').status_code, 401)

    def test_protected_endpoint_requires_a_valid_token(self):
        response = self.client.get('/api/token/me/')

        self.assertEqual(response.status_code, 401)
