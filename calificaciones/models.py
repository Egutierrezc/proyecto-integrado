from django.conf import settings
from django.db import models
from django.db.models import Exists, OuterRef, Q


class QualificationQuerySet(models.QuerySet):
    def visible_to(self, user):
        if not user.is_authenticated:
            return self.none()

        broker_overrides = self.model.objects.filter(
            owner=user,
            origin=self.model.Origin.BROKER,
            market=OuterRef('market'),
            exercise=OuterRef('exercise'),
            instrument=OuterRef('instrument'),
            payment_date=OuterRef('payment_date'),
            event_sequence=OuterRef('event_sequence'),
        )
        return (
            self.filter(Q(owner__isnull=True) | Q(owner=user))
            .annotate(has_broker_override=Exists(broker_overrides))
            .exclude(Q(owner__isnull=True) & Q(has_broker_override=True))
        )


class Qualification(models.Model):
    class Origin(models.TextChoices):
        SYSTEM = 'system', 'Sistema'
        BROKER = 'broker', 'Corredor'

    class EntryMethod(models.TextChoices):
        SYSTEM = 'system', 'Sistema'
        MANUAL = 'manual', 'Ingreso manual'
        FACTOR_FILE = 'factor_file', 'Carga de factores'
        DJ1948_FILE = 'dj1948_file', 'Carga de montos DJ1948'

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='tax_qualifications',
        null=True,
        blank=True,
    )
    origin = models.CharField(max_length=10, choices=Origin.choices)
    entry_method = models.CharField(
        max_length=20,
        choices=EntryMethod.choices,
    )
    market = models.CharField(max_length=3)
    exercise = models.PositiveSmallIntegerField()
    instrument = models.CharField(max_length=50)
    payment_date = models.DateField()
    event_sequence = models.PositiveBigIntegerField()
    description = models.CharField(max_length=200, blank=True)
    payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = QualificationQuerySet.as_manager()

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(
                        origin='system',
                        owner__isnull=True,
                        entry_method='system',
                    )
                    | Q(
                        origin='broker',
                        owner__isnull=False,
                        entry_method__in=('manual', 'factor_file', 'dj1948_file'),
                    )
                ),
                name='qual_origin_owner_method',
            ),
            models.UniqueConstraint(
                fields=(
                    'market',
                    'exercise',
                    'instrument',
                    'payment_date',
                    'event_sequence',
                ),
                condition=Q(origin='system', owner__isnull=True),
                name='uniq_qual_system_event',
            ),
            models.UniqueConstraint(
                fields=(
                    'owner',
                    'market',
                    'exercise',
                    'instrument',
                    'payment_date',
                    'event_sequence',
                ),
                condition=Q(origin='broker', owner__isnull=False),
                name='uniq_qual_broker_event',
            ),
        ]
        ordering = ('exercise', 'instrument', 'payment_date', 'event_sequence')

    def __str__(self):
        return (
            f'{self.market} {self.instrument} {self.exercise} '
            f'{self.payment_date} #{self.event_sequence}'
        )


class QualificationAudit(models.Model):
    class Operation(models.TextChoices):
        CREATE = 'create', 'Creación'
        UPDATE = 'update', 'Modificación'
        DELETE = 'delete', 'Eliminación'

    qualification = models.ForeignKey(
        Qualification,
        on_delete=models.SET_NULL,
        related_name='audit_entries',
        null=True,
        blank=True,
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='tax_qualification_audit_entries',
        null=True,
        blank=True,
    )
    operation = models.CharField(max_length=10, choices=Operation.choices)
    origin = models.CharField(max_length=10, choices=Qualification.Origin.choices)
    entry_method = models.CharField(
        max_length=20,
        choices=Qualification.EntryMethod.choices,
    )
    identity = models.JSONField(default=dict)
    changes = models.JSONField(default=dict)
    occurred_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-occurred_at',)

    def __str__(self):
        return f'{self.get_operation_display()} · {self.occurred_at:%Y-%m-%d %H:%M:%S}'
