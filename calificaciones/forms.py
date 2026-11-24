from decimal import Decimal, InvalidOperation

from django import forms
from django.core.exceptions import ValidationError

from .calculos import (
    CALCULATED_FACTOR_NUMBERS,
    CSV_FACTOR_NUMBERS,
    calculate_factors,
    validate_factor_values,
)


MARKET_CHOICES = (
    ('ACN', 'Acciones'),
    ('CFI', 'CFI'),
    ('FM', 'Fondos mutuos'),
)
ENTRY_MODE_CHOICES = (
    ('factors', 'Ingreso por factores'),
    ('amounts', 'Montos Certificado 70 / 1948'),
)
_FACTOR_QUANTUM = Decimal('0.00000001')


class DecimalInputField(forms.Field):
    widget = forms.NumberInput
    max_input_length = 50

    def to_python(self, value):
        if value in self.empty_values:
            return None
        value = str(value).strip()
        if len(value) > self.max_input_length:
            raise ValidationError('El valor ingresado es demasiado largo.')
        try:
            decimal_value = Decimal(value)
        except (InvalidOperation, TypeError, ValueError) as exc:
            raise ValidationError('Ingresa un número válido.') from exc
        if not decimal_value.is_finite():
            raise ValidationError('El valor debe ser finito.')
        return decimal_value


class AmountCalculationForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for number in CALCULATED_FACTOR_NUMBERS:
            self.fields[f'amount_{number}'] = DecimalInputField(required=False)

    def clean(self):
        cleaned_data = super().clean()
        if self.errors:
            return cleaned_data
        cleaned_data['amount_values'] = {
            number: (
                cleaned_data[f'amount_{number}']
                if cleaned_data[f'amount_{number}'] is not None
                else Decimal(0)
            )
            for number in CALCULATED_FACTOR_NUMBERS
        }
        return cleaned_data


class QualificationEntryForm(forms.Form):
    market = forms.ChoiceField(choices=MARKET_CHOICES)
    exercise = forms.IntegerField(min_value=1, max_value=32767)
    instrument = forms.CharField(max_length=50)
    payment_date = forms.DateField(input_formats=('%Y-%m-%d',))
    event_sequence = forms.IntegerField(min_value=10001)
    description = forms.CharField(max_length=200, required=False)
    dividend_number = forms.IntegerField(min_value=0, required=False, initial=0)
    event_capital = forms.IntegerField(min_value=0, required=False, initial=0)
    historical_value = DecimalInputField(required=False)
    update_factor = DecimalInputField(required=False)
    isfut_isift = forms.BooleanField(required=False)
    entry_mode = forms.ChoiceField(choices=ENTRY_MODE_CHOICES)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for number in CSV_FACTOR_NUMBERS:
            self.fields[f'factor_{number}'] = forms.DecimalField(
                max_digits=9,
                decimal_places=8,
                max_value=Decimal(1),
                required=False,
            )
        self.fields['factor_19B'] = forms.DecimalField(
            max_digits=9,
            decimal_places=8,
            max_value=Decimal(1),
            required=False,
        )
        for number in CALCULATED_FACTOR_NUMBERS:
            self.fields[f'amount_{number}'] = DecimalInputField(required=False)

    def clean(self):
        cleaned_data = super().clean()
        if self.errors:
            return cleaned_data

        amounts = {
            number: (
                cleaned_data[f'amount_{number}']
                if cleaned_data[f'amount_{number}'] is not None
                else Decimal(0)
            )
            for number in CALCULATED_FACTOR_NUMBERS
        }

        if cleaned_data['entry_mode'] == 'amounts':
            calculation = calculate_factors(amounts)
            if not calculation.is_valid:
                for error in calculation.errors:
                    self.add_error(None, error)
                return cleaned_data
            factors = {
                number: (
                    cleaned_data[f'factor_{number}']
                    if cleaned_data[f'factor_{number}'] is not None
                    else calculation.factors[number]
                )
                for number in CALCULATED_FACTOR_NUMBERS
            }
        else:
            factors = {
                number: (
                    cleaned_data[f'factor_{number}']
                    if cleaned_data[f'factor_{number}'] is not None
                    else Decimal(0)
                )
                for number in CALCULATED_FACTOR_NUMBERS
            }

        factors.update(
            {
                number: (
                    cleaned_data[f'factor_{number}']
                    if cleaned_data[f'factor_{number}'] is not None
                    else Decimal(0)
                )
                for number in range(34, 38)
            }
        )
        factors['19B'] = (
            cleaned_data['factor_19B']
            if cleaned_data['factor_19B'] is not None
            else Decimal(0)
        )
        for error in validate_factor_values(factors):
            self.add_error(None, error)

        cleaned_data['amount_values'] = amounts
        cleaned_data['factor_values'] = {
            key: value.quantize(_FACTOR_QUANTUM)
            for key, value in factors.items()
        }
        return cleaned_data
