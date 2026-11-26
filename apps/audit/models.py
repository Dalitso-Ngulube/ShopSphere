from django.db import models


class AuditLog(models.Model):
    # Snapshot identity: audit history must not depend on a live user account.
    actor_id_snapshot = models.CharField(
        max_length=255,
        blank=True,
        db_index=True,
    )
    actor_email_snapshot = models.EmailField(max_length=254, blank=True)

    action = models.CharField(max_length=100, db_index=True)
    object_type = models.CharField(max_length=100)
    object_id = models.CharField(max_length=100)

    before = models.JSONField(null=True, blank=True)
    after = models.JSONField(null=True, blank=True)

    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self) -> str:
        return f"{self.action} on {self.object_type}:{self.object_id}"

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValueError("AuditLog entries are immutable.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError("AuditLog entries cannot be deleted.")
