from django.test import TestCase
from django.contrib.auth.models import User


class HomeTests(TestCase):
    def test_home_requires_login(self):
        response = self.client.get('/home/')

        self.assertRedirects(response, '/?next=/home/')

    def test_home_shows_the_authenticated_user_and_no_example_tax_data(self):
        first_user = User.objects.create_user(username='ana')
        second_user = User.objects.create_user(username='otra-persona')
        self.client.force_login(first_user)

        response = self.client.get('/home/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Hola, ana')
        self.assertContains(response, 'aria-label="Buscar obligaciones"')
        self.assertContains(response, 'ana')
        self.assertNotContains(response, 'María González')
        self.assertNotContains(response, 'Bimestre 3')
        self.assertContains(response, 'Aún no tienes obligaciones registradas.')
        content = response.content.decode()
        self.assertLess(content.index('class="search-box"'), content.index('class="profile"'))

        self.client.force_login(second_user)
        response = self.client.get('/home/')

        self.assertContains(response, 'Hola, otra-persona')
        self.assertNotContains(response, 'Hola, ana')
