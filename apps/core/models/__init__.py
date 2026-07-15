"""Package des modèles de l'application core."""
from apps.core.models.base import (  # noqa: F401
    BaseModel,
    TimeStampedModel,
    UUIDModel,
    AuditModel,
    SoftDeleteModel,
)
