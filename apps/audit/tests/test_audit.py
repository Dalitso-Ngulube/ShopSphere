from django.contrib.auth import get_user_model
from django.db import DatabaseError, connection, transaction
from django.test import TestCase

from apps.audit.models import AuditLog


class AuditLogImmutabilityTests(TestCase):
    def setUp(self):
        self.User = get_user_model()

        self.actor = self.User.objects.create_user(
            username="audit-actor",
            email="actor@example.com",
        )

        self.audit_log = AuditLog.objects.create(
            actor_id_snapshot=str(self.actor.pk),
            actor_email_snapshot=self.actor.email,
            action="product.created",
            object_type="product",
            object_id="123",
            after={"name": "Test product"},
        )

    def test_audit_log_can_be_created(self):
        self.assertTrue(AuditLog.objects.filter(pk=self.audit_log.pk).exists())

    def test_model_save_rejects_updates(self):
        self.audit_log.action = "product.updated"

        with self.assertRaises(ValueError):
            self.audit_log.save()

    def test_model_delete_rejects_deletion(self):
        with self.assertRaises(ValueError):
            self.audit_log.delete()

        self.assertTrue(AuditLog.objects.filter(pk=self.audit_log.pk).exists())

    def test_queryset_update_is_rejected(self):
        with self.assertRaises(DatabaseError), transaction.atomic():
            AuditLog.objects.filter(pk=self.audit_log.pk).update(action="product.updated")

        self.audit_log.refresh_from_db()
        self.assertEqual(self.audit_log.action, "product.created")

    def test_queryset_delete_is_rejected(self):
        with self.assertRaises(DatabaseError), transaction.atomic():
            AuditLog.objects.filter(pk=self.audit_log.pk).delete()

        self.assertTrue(AuditLog.objects.filter(pk=self.audit_log.pk).exists())

    def test_truncate_is_rejected(self):
        with (
            self.assertRaises(DatabaseError),
            transaction.atomic(),
            connection.cursor() as cursor,
        ):
            cursor.execute("TRUNCATE TABLE audit_auditlog")

        self.assertTrue(AuditLog.objects.filter(pk=self.audit_log.pk).exists())

    def test_user_deletion_preserves_audit_record(self):
        original_actor_id = self.audit_log.actor_id_snapshot
        original_email = self.audit_log.actor_email_snapshot

        self.actor.delete()

        self.audit_log.refresh_from_db()

        self.assertEqual(self.audit_log.actor_id_snapshot, original_actor_id)
        self.assertEqual(self.audit_log.actor_email_snapshot, original_email)
        self.assertTrue(AuditLog.objects.filter(pk=self.audit_log.pk).exists())
