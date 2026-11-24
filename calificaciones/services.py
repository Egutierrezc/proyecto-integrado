from collections.abc import Mapping
from typing import Any

from django.contrib.auth.models import AbstractBaseUser

from .models import Qualification, QualificationAudit


def record_qualification_audit(
    *,
    qualification: Qualification,
    actor: AbstractBaseUser | None,
    operation: str,
    changes: Mapping[str, Any] | None = None,
) -> QualificationAudit:
    identity = {
        'market': qualification.market,
        'exercise': qualification.exercise,
        'instrument': qualification.instrument,
        'payment_date': qualification.payment_date.isoformat(),
        'event_sequence': qualification.event_sequence,
        'owner_id': qualification.owner_id,
    }
    return QualificationAudit.objects.create(
        qualification=qualification,
        actor=actor,
        operation=operation,
        origin=qualification.origin,
        entry_method=qualification.entry_method,
        identity=identity,
        changes=changes if changes is not None else {},
    )
