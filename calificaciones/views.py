from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from .calculos import CSV_FACTOR_NUMBERS, FACTOR_LABELS, calculate_factors
from .forms import AmountCalculationForm, QualificationEntryForm
from .models import Qualification, QualificationAudit
from .services import record_qualification_audit


MANUAL_FACTOR_LABELS = {
    34: 'Crédito por impuesto tasa adicional, Ex. Art. 21 LIR.',
    35: 'Tasa Efectiva del credito del FUT (TEF)',
    36: 'TASA EFECTIVA DEL CRÉDITO DEL FUNT (TEX)',
    37: 'DEVOLUCION DE CAPITAL ART.17 N° 7 LIR.',
    '19B': 'Ingreso no Constitutivo de Renta',
}
COMMERCIAL_YEARS = range(2020, 2031)
MARKET_CODES = {'ACN', 'CFI', 'FM'}
ORIGIN_CODES = {
    Qualification.Origin.SYSTEM,
    Qualification.Origin.BROKER,
}


def _form_errors(form):
    return [
        str(error)
        for field_errors in form.errors.values()
        for error in field_errors
    ]


def _decimal_text(value):
    return format(value, 'f') if value is not None else ''


def _qualification_row(qualification):
    payload = qualification.payload
    factors = payload.get('factors', {})
    if not isinstance(factors, dict):
        raise ValueError(
            f'La calificación {qualification.pk} contiene factores inválidos.'
        )
    return {
        'qualification': qualification,
        'update_factor': payload.get('update_factor', ''),
        'factor_values': [
            str(factors.get(str(number), ''))
            for number in CSV_FACTOR_NUMBERS
        ],
        'isfut_isift': 'Sí' if payload.get('isfut_isift', False) else 'No',
    }


@login_required
def mantenedor(request):
    selected_market = request.GET.get('market', '')
    selected_origin = request.GET.get('origin', '')
    selected_year = request.GET.get('year', '')
    selected_year_value = ''

    if selected_market and selected_market not in MARKET_CODES:
        return HttpResponseBadRequest('El mercado seleccionado no es válido.')
    if selected_origin and selected_origin not in ORIGIN_CODES:
        return HttpResponseBadRequest('El origen seleccionado no es válido.')

    qualifications = Qualification.objects.visible_to(request.user)
    if selected_market:
        qualifications = qualifications.filter(market=selected_market)
    if selected_origin:
        qualifications = qualifications.filter(origin=selected_origin)
    if selected_year:
        try:
            exercise = int(selected_year)
        except ValueError:
            return HttpResponseBadRequest('El período comercial no es válido.')
        if not 1 <= exercise <= 32767:
            return HttpResponseBadRequest('El período comercial no es válido.')
        qualifications = qualifications.filter(exercise=exercise)
        selected_year_value = exercise

    grid_factor_fields = [
        (
            number,
            FACTOR_LABELS[number]
            if number in FACTOR_LABELS
            else MANUAL_FACTOR_LABELS[number],
        )
        for number in CSV_FACTOR_NUMBERS
    ]
    qualification_rows = [
        _qualification_row(qualification)
        for qualification in qualifications
    ]
    return render(
        request,
        'calificaciones/mantenedor.html',
        {
            'factor_fields': FACTOR_LABELS.items(),
            'manual_factor_fields': MANUAL_FACTOR_LABELS.items(),
            'grid_factor_fields': grid_factor_fields,
            'amount_fields': range(8, 34),
            'commercial_years': COMMERCIAL_YEARS,
            'selected_market': selected_market,
            'selected_origin': selected_origin,
            'selected_year': selected_year_value,
            'qualification_rows': qualification_rows,
            'result_count': len(qualification_rows),
            'display_name': request.user.get_full_name() or request.user.get_username(),
        },
    )


@login_required
@require_POST
def calcular_factores(request):
    form = AmountCalculationForm(request.POST)
    if not form.is_valid():
        return JsonResponse({'errors': _form_errors(form)}, status=400)

    calculation = calculate_factors(form.cleaned_data['amount_values'])
    if not calculation.is_valid:
        return JsonResponse({'errors': list(calculation.errors)}, status=422)

    return JsonResponse(
        {
            'denominator': _decimal_text(calculation.denominator),
            'factors': {
                str(number): _decimal_text(value)
                for number, value in calculation.factors.items()
            },
        }
    )


@login_required
@require_POST
def ingresar_calificacion(request):
    form = QualificationEntryForm(request.POST)
    if not form.is_valid():
        return JsonResponse({'errors': _form_errors(form)}, status=400)

    values = form.cleaned_data
    mode = values['entry_mode']
    payload = {
        'entry_mode': mode,
        'source_form': (
            'certificado_70_1948' if mode == 'amounts' else 'manual_factors'
        ),
        'dividend_number': values['dividend_number'] or 0,
        'event_capital': values['event_capital'] or 0,
        'historical_value': _decimal_text(values['historical_value']),
        'update_factor': _decimal_text(values['update_factor'] or 0),
        'isfut_isift': values['isfut_isift'],
        'amounts': (
            {
                str(number): _decimal_text(amount)
                for number, amount in values['amount_values'].items()
            }
            if mode == 'amounts'
            else {}
        ),
        'factors': {
            str(number): _decimal_text(factor)
            for number, factor in values['factor_values'].items()
        },
    }
    identity = {
        'market': values['market'],
        'exercise': values['exercise'],
        'instrument': values['instrument'],
        'payment_date': values['payment_date'],
        'event_sequence': values['event_sequence'],
    }

    try:
        with transaction.atomic():
            qualification = Qualification.objects.create(
                **identity,
                description=values['description'],
                owner=request.user,
                origin=Qualification.Origin.BROKER,
                entry_method=Qualification.EntryMethod.MANUAL,
                payload=payload,
            )
            record_qualification_audit(
                qualification=qualification,
                actor=request.user,
                operation=QualificationAudit.Operation.CREATE,
                changes={
                    'created': {
                        **{
                            key: value.isoformat() if hasattr(value, 'isoformat') else value
                            for key, value in identity.items()
                        },
                        'description': values['description'],
                        'payload': payload,
                    }
                },
            )
    except IntegrityError:
        duplicate_exists = Qualification.objects.filter(
            **identity,
            owner=request.user,
            origin=Qualification.Origin.BROKER,
        ).exists()
        if duplicate_exists:
            return JsonResponse(
                {
                    'errors': [
                        'Ya existe una calificación local con esa identidad para este corredor.'
                    ]
                },
                status=409,
            )
        raise

    return JsonResponse(
        {
            'id': qualification.pk,
            'message': 'La calificación se guardó correctamente.',
        },
        status=201,
    )
