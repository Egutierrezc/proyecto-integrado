from datetime import date

from django.test import TestCase
from django.contrib.auth.models import User

from calificaciones.models import Qualification


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
        self.assertContains(response, 'accounts/logout.js')
        self.assertContains(response, 'Hola, ana')
        self.assertContains(response, 'Calificaciones visibles')
        self.assertContains(response, 'Calificaciones recientes')
        self.assertContains(response, 'aria-label="Resumen de calificaciones"')
        self.assertContains(response, 'ana')
        self.assertNotContains(response, 'María González')
        self.assertNotContains(response, 'Bimestre 3')
        self.assertContains(response, 'Aún no hay calificaciones para mostrar.')
        self.assertContains(response, 'Ingresa la primera calificación')
        self.assertNotContains(response, 'Tus obligaciones')
        self.assertEqual(response.context['qualification_count'], 0)
        content = response.content.decode()
        self.assertNotIn('class="search-box"', content)

        self.client.force_login(second_user)
        response = self.client.get('/home/')

        self.assertContains(response, 'Hola, otra-persona')
        self.assertNotContains(response, 'Hola, ana')

    def test_home_shows_only_visible_qualifications_and_counts(self):
        user = User.objects.create_user(username='corredor')
        other_user = User.objects.create_user(username='otro-corredor')
        shared_identity = {
            'market': 'ACN',
            'exercise': 2025,
            'instrument': 'COPEC',
            'payment_date': date(2025, 4, 1),
            'event_sequence': 10001,
        }
        system_override = Qualification.objects.create(
            **shared_identity,
            origin=Qualification.Origin.SYSTEM,
            entry_method=Qualification.EntryMethod.SYSTEM,
        )
        broker_override = Qualification.objects.create(
            **shared_identity,
            owner=user,
            origin=Qualification.Origin.BROKER,
            entry_method=Qualification.EntryMethod.MANUAL,
            description='Registro local',
        )
        system_record = Qualification.objects.create(
            **(shared_identity | {'instrument': 'ENEL', 'event_sequence': 10002}),
            origin=Qualification.Origin.SYSTEM,
            entry_method=Qualification.EntryMethod.SYSTEM,
        )
        Qualification.objects.create(
            **(shared_identity | {'instrument': 'FALABELLA', 'event_sequence': 10003}),
            owner=other_user,
            origin=Qualification.Origin.BROKER,
            entry_method=Qualification.EntryMethod.MANUAL,
        )
        self.client.force_login(user)

        response = self.client.get('/home/')

        self.assertEqual(response.context['qualification_count'], 2)
        self.assertEqual(response.context['broker_qualification_count'], 1)
        self.assertEqual(response.context['system_qualification_count'], 1)
        shown_ids = {
            qualification.pk
            for qualification in response.context['recent_qualifications']
        }
        self.assertEqual(shown_ids, {broker_override.pk, system_record.pk})
        self.assertNotIn(system_override.pk, shown_ids)
        self.assertContains(response, 'Registro local')
        self.assertNotContains(response, 'FALABELLA')
