from datetime import date
from decimal import Decimal

from django.contrib.auth.models import AnonymousUser, User
from django.db import IntegrityError, transaction
from django.test import SimpleTestCase, TestCase

from .calculos import (
    CALCULATED_FACTOR_NUMBERS,
    CSV_FACTOR_NUMBERS,
    FACTOR_NUMBERS,
    MANUAL_ONLY_FACTOR_NUMBERS,
    calculate_factors,
)
from .models import Qualification, QualificationAudit
from .services import record_qualification_audit


class CalculateFactorsTests(SimpleTestCase):
    def make_amounts(self):
        return {number: Decimal(0) for number in CALCULATED_FACTOR_NUMBERS}

    def test_csv_factor_columns_are_8_to_37_and_exclude_manual_only_19b(self):
        self.assertEqual(CSV_FACTOR_NUMBERS, tuple(range(8, 38)))
        self.assertEqual(len(CSV_FACTOR_NUMBERS), 30)
        self.assertEqual(MANUAL_ONLY_FACTOR_NUMBERS, ('19B',))
        self.assertNotIn('19B', CSV_FACTOR_NUMBERS)

    def test_calculates_26_factors_and_rounds_to_eight_decimal_places(self):
        amounts = self.make_amounts()
        amounts.update({8: Decimal(1), 9: Decimal(2), 10: Decimal(1)})
        amounts[19] = Decimal(8)

        result = calculate_factors(amounts)

        self.assertEqual(len(result.factors), 26)
        self.assertEqual(set(result.factors), set(FACTOR_NUMBERS))
        self.assertEqual(result.denominator, Decimal(12))
        self.assertEqual(result.factors[8], Decimal('0.08333333'))
        self.assertEqual(result.factors[9], Decimal('0.16666667'))
        self.assertNotIn(34, result.factors)
        self.assertTrue(result.is_valid)

    def test_accepts_factor_and_sum_equal_to_one(self):
        amounts = self.make_amounts()
        amounts[8] = Decimal(1)

        result = calculate_factors(amounts)

        self.assertTrue(result.is_valid)
        self.assertEqual(result.factors[8], Decimal('1.00000000'))
        self.assertEqual(
            sum(
                result.factors[number]
                for number in range(8, 20)
            ),
            Decimal('1.00000000'),
        )

    def test_zero_denominator_leaves_calculated_factors_unavailable(self):
        result = calculate_factors(self.make_amounts())

        self.assertEqual(result.denominator, Decimal(0))
        self.assertTrue(
            all(result.factors[number] is None for number in CALCULATED_FACTOR_NUMBERS)
        )
        self.assertIn('suma de los montos 8–19 es 0', result.errors[0])
        self.assertFalse(result.is_valid)

    def test_validates_factor_limit_without_rejecting_sum_8_to_19_equal_to_one(self):
        amounts = self.make_amounts()
        amounts.update({8: Decimal(2), 9: Decimal(2)})
        amounts[19] = Decimal(-3)

        result = calculate_factors(amounts)

        self.assertIn('El factor 8 no puede ser mayor que 1.', result.errors)
        self.assertNotIn(
            'La suma de los factores 8–19 no puede ser mayor que 1.',
            result.errors,
        )

    def test_validates_rounded_sum_of_factors_8_to_19(self):
        amounts = self.make_amounts()
        values = (
            32562, 23563, 91619, 31995, 10729, 75291,
            39355, 68839, 64896, 45021, 95610, 58830,
        )
        amounts.update(
            {
                number: Decimal(value)
                for number, value in zip(range(8, 20), values)
            }
        )

        result = calculate_factors(amounts)

        self.assertIn(
            'La suma de los factores 8–19 no puede ser mayor que 1.',
            result.errors,
        )

    def test_rejects_missing_amounts_and_factor_ids_outside_scope(self):
        amounts = self.make_amounts()
        del amounts[12]
        with self.assertRaisesMessage(ValueError, '12'):
            calculate_factors(amounts)

        amounts = self.make_amounts()
        amounts[34] = Decimal(0)
        with self.assertRaisesMessage(ValueError, 'Solo se aceptan montos homologados'):
            calculate_factors(amounts)

    def test_rejects_non_finite_amounts_and_factors_above_one(self):
        amounts = self.make_amounts()
        amounts[8] = Decimal('NaN')
        with self.assertRaisesMessage(ValueError, 'debe ser finito'):
            calculate_factors(amounts)

        amounts = self.make_amounts()
        amounts[8] = 0.1
        with self.assertRaisesMessage(ValueError, 'no es un monto válido'):
            calculate_factors(amounts)

        amounts = self.make_amounts()
        amounts[8] = Decimal(1)
        amounts[9] = Decimal(-2)
        result = calculate_factors(amounts)
        self.assertIn('El factor 9 no puede ser mayor que 1.', result.errors)


class MantenedorPrototypeTests(TestCase):
    def test_mantenedor_requires_authentication(self):
        response = self.client.get('/calificaciones/')

        self.assertRedirects(
            response,
            '/?next=/calificaciones/',
        )

    def test_mantenedor_renders_mockup_structure_and_manual_factors(self):
        user = User.objects.create_user(username='corredor')
        self.client.force_login(user)

        response = self.client.get('/calificaciones/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'home/styles.css')
        self.assertContains(response, 'accounts/logout.js')
        self.assertContains(response, 'class="layout"')
        self.assertContains(response, 'class="sidebar"')
        self.assertContains(response, 'aria-current="page"')
        self.assertContains(response, 'class="topbar"')
        self.assertContains(response, 'class="profile"')
        self.assertNotContains(response, 'Buscar calificaciones...')
        self.assertContains(response, 'corredor')
        self.assertContains(response, 'Buscar calificaciones')
        self.assertContains(response, 'Período comercial')
        self.assertContains(response, 'Calificación pendiente')
        self.assertContains(response, 'Carga x factor')
        self.assertContains(response, 'Carga x monto')
        self.assertContains(response, 'id="basic-form" novalidate')
        self.assertNotContains(response, 'method="dialog"')
        self.assertContains(response, 'data-tab="amounts"')
        self.assertContains(response, 'Montos base del cálculo')
        self.assertContains(response, 'Calcula antes de grabar')
        self.assertContains(
            response,
            'type="button" data-close-dialog aria-label="Cerrar"',
        )
        self.assertContains(
            response,
            'type="button" data-close-dialog>Cancelar</button>',
        )
        self.assertContains(response, 'PASO 1 DE 2')
        self.assertContains(response, 'PASO 2 DE 2')
        self.assertContains(response, 'Certificado 70 / 1948')
        self.assertContains(response, 'no se aplica al Certificado 44 / 1922')
        self.assertContains(response, 'DJ1949')
        self.assertContains(response, 'Factores 8–37')
        self.assertContains(
            response,
            'Con crédito por IDPC generados a contar del 01.01.2017',
        )
        self.assertContains(response, 'Rentas provenientes del registro RAP')
        self.assertContains(
            response,
            'TASA EFECTIVA DEL CRÉDITO DEL FUNT (TEX)',
        )
        self.assertContains(response, 'Acogido ISFUT / ISIFT')
        self.assertContains(response, 'Factor 34')
        self.assertContains(response, 'Factor 37')
        self.assertContains(response, 'Factor 19B')
        self.assertContains(response, '34–37 son manuales')
        self.assertContains(response, 'fuera del CSV')
        self.assertContains(response, 'Ingreso manual')
        self.assertEqual(len(response.context['factor_fields']), 26)
        self.assertEqual(len(response.context['grid_factor_fields']), 30)
        self.assertEqual(len(response.context['manual_factor_fields']), 5)
        self.assertEqual(list(response.context['amount_fields']), list(range(8, 34)))
        self.assertContains(
            response,
            'No hay calificaciones que coincidan con los filtros seleccionados.',
        )


class QualificationIdentityTests(TestCase):
    def setUp(self):
        self.broker = User.objects.create_user(username='corredor-a')
        self.other_broker = User.objects.create_user(username='corredor-b')
        self.key = {
            'market': 'ACN',
            'exercise': 2025,
            'instrument': 'COPEC',
            'payment_date': date(2025, 4, 1),
            'event_sequence': 100001,
        }

    def create_system_qualification(self):
        return Qualification.objects.create(
            **self.key,
            origin=Qualification.Origin.SYSTEM,
            entry_method=Qualification.EntryMethod.SYSTEM,
        )

    def create_broker_qualification(self, owner=None, **key_changes):
        return Qualification.objects.create(
            **(self.key | key_changes),
            owner=owner or self.broker,
            origin=Qualification.Origin.BROKER,
            entry_method=Qualification.EntryMethod.MANUAL,
        )

    def test_broker_override_is_local_and_system_record_is_preserved(self):
        system_record = self.create_system_qualification()
        broker_record = self.create_broker_qualification()

        visible_to_owner = list(Qualification.objects.visible_to(self.broker))
        visible_to_other_broker = list(
            Qualification.objects.visible_to(self.other_broker)
        )

        self.assertEqual(visible_to_owner, [broker_record])
        self.assertEqual(visible_to_other_broker, [system_record])
        self.assertTrue(
            Qualification.objects.filter(pk=system_record.pk).exists()
        )

    def test_broker_without_override_sees_system_record(self):
        system_record = self.create_system_qualification()

        visible = list(Qualification.objects.visible_to(self.broker))

        self.assertEqual(visible, [system_record])
        self.assertEqual(list(Qualification.objects.visible_to(AnonymousUser())), [])

    def test_identity_is_unique_per_system_and_per_broker(self):
        self.create_system_qualification()
        self.create_broker_qualification()
        self.create_broker_qualification(owner=self.other_broker)

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self.create_system_qualification()

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self.create_broker_qualification()

    def test_owner_and_origin_must_match(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Qualification.objects.create(
                    **self.key,
                    owner=self.broker,
                    origin=Qualification.Origin.SYSTEM,
                    entry_method=Qualification.EntryMethod.SYSTEM,
                )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Qualification.objects.create(
                    **self.key,
                    origin=Qualification.Origin.BROKER,
                    entry_method=Qualification.EntryMethod.MANUAL,
                )

    def test_audit_identity_survives_qualification_deletion(self):
        qualification = self.create_broker_qualification()

        audit = record_qualification_audit(
            qualification=qualification,
            actor=self.broker,
            operation=QualificationAudit.Operation.CREATE,
            changes={'description': {'before': '', 'after': 'Dividendo'}},
        )
        qualification.delete()
        audit.refresh_from_db()

        self.assertIsNone(audit.qualification)
        self.assertEqual(audit.actor, self.broker)
        self.assertEqual(audit.identity['instrument'], 'COPEC')
        self.assertEqual(audit.identity['owner_id'], self.broker.pk)
        self.assertEqual(audit.changes['description']['after'], 'Dividendo')


class QualificationEntryFlowTests(TestCase):
    def setUp(self):
        self.broker = User.objects.create_user(username='ingreso-corredor')
        self.client.force_login(self.broker)
        self.entry_data = {
            'market': 'ACN',
            'exercise': '2025',
            'instrument': 'COPEC',
            'payment_date': '2025-04-01',
            'event_sequence': '100001',
            'description': 'Dividendo de prueba',
            'dividend_number': '1',
            'event_capital': '0',
            'historical_value': '125.50',
            'update_factor': '1.00000000',
            'entry_mode': 'amounts',
        }

    def add_zero_amounts(self, data=None):
        data = data if data is not None else self.entry_data
        for number in CALCULATED_FACTOR_NUMBERS:
            data[f'amount_{number}'] = '0'
        data['calculation_confirmed'] = 'true'
        return data

    def test_amount_entry_requires_all_amounts_and_a_calculation(self):
        incomplete_data = self.add_zero_amounts(self.entry_data.copy())
        incomplete_data['amount_8'] = '1'
        del incomplete_data['amount_33']

        incomplete_response = self.client.post(
            '/calificaciones/ingresar/',
            incomplete_data,
        )

        self.assertEqual(incomplete_response.status_code, 400)
        self.assertIn(
            'Ingresa un monto; escribe 0 si no corresponde.',
            incomplete_response.json()['errors'],
        )
        self.assertFalse(Qualification.objects.exists())

        uncalculated_data = self.add_zero_amounts(self.entry_data.copy())
        uncalculated_data['amount_8'] = '1'
        uncalculated_data.pop('calculation_confirmed')

        uncalculated_response = self.client.post(
            '/calificaciones/ingresar/',
            uncalculated_data,
        )

        self.assertEqual(uncalculated_response.status_code, 400)
        self.assertIn(
            'Completa los montos 8–33 y calcula los factores antes de grabar.',
            uncalculated_response.json()['errors'],
        )
        self.assertFalse(Qualification.objects.exists())

    def test_amount_entry_calculates_saves_audits_and_lists_local_record(self):
        data = self.add_zero_amounts()
        data['amount_8'] = '1'
        data['amount_9'] = '3'

        response = self.client.post('/calificaciones/ingresar/', data)

        self.assertEqual(response.status_code, 201)
        qualification = Qualification.objects.get(owner=self.broker)
        self.assertEqual(qualification.origin, Qualification.Origin.BROKER)
        self.assertEqual(
            qualification.entry_method,
            Qualification.EntryMethod.MANUAL,
        )
        self.assertEqual(qualification.payload['source_form'], 'certificado_70_1948')
        self.assertEqual(qualification.payload['factors']['8'], '0.25000000')
        self.assertEqual(qualification.payload['factors']['9'], '0.75000000')
        self.assertEqual(qualification.payload['amounts']['8'], '1')
        audit = QualificationAudit.objects.get(qualification=qualification)
        self.assertEqual(audit.actor, self.broker)
        self.assertEqual(audit.operation, QualificationAudit.Operation.CREATE)

        list_response = self.client.get('/calificaciones/')
        self.assertContains(list_response, 'COPEC')
        self.assertContains(list_response, '0.25000000')
        self.assertEqual(list_response.context['result_count'], 1)

    def test_manual_factor_entry_saves_without_amount_calculation(self):
        data = self.entry_data.copy()
        data['entry_mode'] = 'factors'
        for number in CSV_FACTOR_NUMBERS:
            data[f'factor_{number}'] = '0'
        data['factor_19B'] = '0.125'

        response = self.client.post('/calificaciones/ingresar/', data)

        self.assertEqual(response.status_code, 201)
        qualification = Qualification.objects.get(owner=self.broker)
        self.assertEqual(qualification.payload['source_form'], 'manual_factors')
        self.assertEqual(qualification.payload['factors']['19B'], '0.12500000')

    def test_manual_entry_rejects_factor_sum_above_one(self):
        data = self.entry_data.copy()
        data['entry_mode'] = 'factors'
        for number in CSV_FACTOR_NUMBERS:
            data[f'factor_{number}'] = '0'
        data['factor_8'] = '0.8'
        data['factor_9'] = '0.20000001'
        data['factor_19B'] = '0'

        response = self.client.post('/calificaciones/ingresar/', data)

        self.assertEqual(response.status_code, 400)
        self.assertIn(
            'La suma de los factores 8–19 no puede ser mayor que 1.',
            response.json()['errors'],
        )
        self.assertFalse(Qualification.objects.exists())

    def test_duplicate_identity_returns_conflict_without_duplicate_audit(self):
        data = self.add_zero_amounts()
        data['amount_8'] = '1'
        first_response = self.client.post('/calificaciones/ingresar/', data)
        second_response = self.client.post('/calificaciones/ingresar/', data)

        self.assertEqual(first_response.status_code, 201)
        self.assertEqual(second_response.status_code, 409)
        self.assertEqual(Qualification.objects.filter(owner=self.broker).count(), 1)
        self.assertEqual(QualificationAudit.objects.count(), 1)

    def test_calculation_endpoint_returns_factors_and_rejects_zero_denominator(self):
        data = {
            f'amount_{number}': '0'
            for number in CALCULATED_FACTOR_NUMBERS
        }
        data['amount_8'] = '1'
        data['amount_9'] = '3'

        response = self.client.post('/calificaciones/calcular/', data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['factors']['8'], '0.25000000')
        self.assertEqual(response.json()['factors']['9'], '0.75000000')

        zero_response = self.client.post(
            '/calificaciones/calcular/',
            {
                f'amount_{number}': '0'
                for number in CALCULATED_FACTOR_NUMBERS
            },
        )
        self.assertEqual(zero_response.status_code, 422)
        self.assertIn('es 0', zero_response.json()['errors'][0])

        incomplete_response = self.client.post(
            '/calificaciones/calcular/',
            {'amount_8': '1'},
        )
        self.assertEqual(incomplete_response.status_code, 400)
        self.assertIn(
            'Ingresa un monto; escribe 0 si no corresponde.',
            incomplete_response.json()['errors'],
        )
