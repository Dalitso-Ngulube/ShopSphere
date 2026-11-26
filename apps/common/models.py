from django.db import models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class IdempotencyKey(TimeStampedModel):
    """
    Stored in common without a foreign key to accounts.User (S10)
    so common remains dependency-free.
    """

    owner_ref = models.CharField(max_length=128)
    scope = models.CharField(max_length=64)
    key = models.CharField(max_length=128)
    request_hash = models.CharField(max_length=64)
    response_status = models.PositiveSmallIntegerField()
    response_body = models.JSONField()
    expires_at = models.DateTimeField(db_index=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["owner_ref", "scope", "key"],
                name="uq_idempotency_owner_scope_key",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.scope}:{self.owner_ref}:<redacted>"
