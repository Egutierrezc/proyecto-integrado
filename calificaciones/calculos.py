from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


FACTOR_NUMBERS = tuple(range(8, 34))
CALCULATED_FACTOR_NUMBERS = FACTOR_NUMBERS
CSV_FACTOR_NUMBERS = tuple(range(8, 38))
MANUAL_ONLY_FACTOR_NUMBERS = ('19B',)
DENOMINATOR_AMOUNT_NUMBERS = tuple(range(8, 20))
FACTOR_SUM_VALIDATION_NUMBERS = tuple(range(8, 20))
FACTOR_LABELS = {
    8: 'Con crédito por IDPC generados a contar del 01.01.2017',
    9: 'Con crédito por IDPC acumulados hasta el 31.12.2016',
    10: 'Con derecho a crédito por pago de IDPC voluntario',
    11: 'Sin derecho a crédito',
    12: (
        'Rentas provenientes del registro RAP y Diferencia Inicial de sociedad '
        'acogida al ex Art. 14 TER A) LIR'
    ),
    13: 'Otras rentas percibidas Sin Prioridad en su orden de imputación',
    14: 'Exceso Distribuciones Desproporcionadas (N°9 Art.14 A)',
    15: (
        'Utilidades afectadas con impuesto sustitutivo al FUT (ISFUT) '
        'Ley N°20.780'
    ),
    16: (
        'Rentas generadas hasta el 31.12.1983 y/o utilidades afectadas con '
        'impuesto sustitutivo al FUT (ISFUT) LEY N°21.210'
    ),
    17: (
        'Rentas Exentas de Impuesto Global Complementario (IGC) '
        '(Artículo 11, Ley 18.401), Afectas a Impuesto Adicional'
    ),
    18: (
        'Rentas Exentas de Impuesto Global Complementario (IGC) y/o '
        'Impuesto Adicional (IA)'
    ),
    19: 'Ingresos No Constitutivos de Renta',
    20: (
        'Acumulados a Contar del 01.01.2017 · Asociados a Rentas Afectas · '
        'No Sujetos a Restitución generados Hasta el 31.12.2019 · '
        'Sin derecho a devolución'
    ),
    21: (
        'Acumulados a Contar del 01.01.2017 · Asociados a Rentas Afectas · '
        'No Sujetos a Restitución generados Hasta el 31.12.2019 · '
        'Con derecho a devolución'
    ),
    22: (
        'Acumulados a Contar del 01.01.2017 · Asociados a Rentas Afectas · '
        'No Sujetos a Restitución generados a contar del 01.01.2020 · '
        'Sin derecho a devolución'
    ),
    23: (
        'Acumulados a Contar del 01.01.2017 · Asociados a Rentas Afectas · '
        'No Sujetos a Restitución generados a contar del 01.01.2020 · '
        'Con derecho a devolución'
    ),
    24: (
        'Acumulados a Contar del 01.01.2017 · Asociados a Rentas Afectas · '
        'Sujetos a Restitución · Sin derecho a devolución'
    ),
    25: (
        'Acumulados a Contar del 01.01.2017 · Asociados a Rentas Afectas · '
        'Sujetos a Restitución · Con derecho a devolución'
    ),
    26: (
        'Acumulados a Contar del 01.01.2017 · Asociados a Rentas Exentas · '
        'Sujetos a Restitución · Sin derecho a devolución'
    ),
    27: (
        'Acumulados a Contar del 01.01.2017 · Asociados a Rentas Exentas · '
        'Sujetos a Restitución · Con derecho a devolución'
    ),
    28: 'Acumulados a Contar del 01.01.2017 · Crédito por IPE',
    29: (
        'Acumulados Hasta el 31.12.2016 · Asociados a Rentas Afectas · '
        'Sin derecho a devolución'
    ),
    30: (
        'Acumulados Hasta el 31.12.2016 · Asociados a Rentas Afectas · '
        'Con derecho a devolución'
    ),
    31: (
        'Acumulados Hasta el 31.12.2016 · Asociados a Rentas Exentas '
        '(artículo 11, Ley 18.401) · Sin derecho a devolución'
    ),
    32: (
        'Acumulados Hasta el 31.12.2016 · Asociados a Rentas Exentas '
        '(artículo 11, Ley 18.401) · Con derecho a devolución'
    ),
    33: 'Acumulados Hasta el 31.12.2016 · Crédito por IPE',
}
_FACTOR_QUANTUM = Decimal('0.00000001')


@dataclass(frozen=True)
class FactorCalculation:
    denominator: Decimal
    factors: dict[int, Decimal | None]
    errors: tuple[str, ...]

    @property
    def is_valid(self) -> bool:
        return not self.errors


def _decimal_values(values: Mapping[int, Decimal | int | str]) -> dict[int, Decimal]:
    result = {}
    for number, value in values.items():
        if isinstance(value, (bool, float)):
            raise ValueError(f'El valor para el campo {number} no es un monto válido.')
        try:
            result[number] = Decimal(value)
        except (InvalidOperation, TypeError, ValueError) as exc:
            raise ValueError(
                f'El valor para el campo {number} no es un monto válido.'
            ) from exc
        if not result[number].is_finite():
            raise ValueError(f'El valor para el campo {number} debe ser finito.')
    return result


def validate_factor_values(
    factors: Mapping[int | str, Decimal | None],
) -> tuple[str, ...]:
    errors = [
        f'El factor {number} no puede ser mayor que 1.'
        for number, value in factors.items()
        if value is not None and value > 1
    ]
    factors_8_to_19 = [
        factors.get(number) for number in FACTOR_SUM_VALIDATION_NUMBERS
    ]
    if all(value is not None for value in factors_8_to_19):
        if sum(factors_8_to_19, start=Decimal(0)) > 1:
            errors.append('La suma de los factores 8–19 no puede ser mayor que 1.')
    return tuple(errors)


def calculate_factors(
    amounts: Mapping[int, Decimal | int | str],
) -> FactorCalculation:
    """Calcula los factores 8–33.

    Las llaves de ``amounts`` representan las columnas de monto homologadas.
    Cada factor 8–33 usa el monto de su misma columna como numerador; el
    denominador es la suma de las columnas 8–19, según la hoja de homologación.
    Los factores posteriores al 33 quedan fuera del alcance actual.
    """
    amount_values = _decimal_values(amounts)

    unexpected_amounts = sorted(
        set(amount_values) - set(CALCULATED_FACTOR_NUMBERS)
    )
    if unexpected_amounts:
        raise ValueError(
            'Solo se aceptan montos homologados para las columnas 8–33; '
            'recibidas: ' + ', '.join(map(str, unexpected_amounts))
        )

    missing_amounts = sorted(
        set(CALCULATED_FACTOR_NUMBERS) - amount_values.keys()
    )
    if missing_amounts:
        raise ValueError(
            'Faltan montos homologados para las columnas: '
            + ', '.join(map(str, missing_amounts))
        )

    denominator = sum(
        (amount_values[number] for number in DENOMINATOR_AMOUNT_NUMBERS),
        start=Decimal(0),
    )
    factors: dict[int, Decimal | None] = {number: None for number in FACTOR_NUMBERS}
    errors = []

    if denominator == 0:
        errors.append(
            'No se pueden calcular los factores 8–33: la suma de los montos '
            '8–19 es 0.'
        )
    else:
        for number in CALCULATED_FACTOR_NUMBERS:
            factors[number] = (
                amount_values[number] / denominator
            ).quantize(_FACTOR_QUANTUM, rounding=ROUND_HALF_UP)

    errors.extend(validate_factor_values(factors))

    return FactorCalculation(
        denominator=denominator,
        factors=factors,
        errors=tuple(errors),
    )
