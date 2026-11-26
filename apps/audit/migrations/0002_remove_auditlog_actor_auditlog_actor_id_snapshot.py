from django.conf import settings
from django.db import migrations, models
from django.core.exceptions import FieldDoesNotExist

BATCH_SIZE = 500


def copy_actor_ids_forward(apps, schema_editor):
    AuditLog = apps.get_model("audit", "AuditLog")
    User = apps.get_model(*settings.AUTH_USER_MODEL.split("."))

    database = schema_editor.connection.alias
    batch_size = 500

    # Historical migration models may not expose get_email_field_name().
    # Use the configured EMAIL_FIELD where available.
    email_field_name = getattr(User, "EMAIL_FIELD", "email")

    try:
        User._meta.get_field(email_field_name)
        has_email_field = True
    except FieldDoesNotExist:
        has_email_field = False

    queryset = AuditLog.objects.using(database).filter(actor__isnull=False)

    if has_email_field:
        queryset = queryset.values_list(
            "pk",
            "actor_id",
            f"actor__{email_field_name}",
        )
    else:
        queryset = queryset.values_list(
            "pk",
            "actor_id",
        )

    batch = []

    for row in queryset.iterator(chunk_size=batch_size):
        audit_log = AuditLog(pk=row[0])
        audit_log.actor_id_snapshot = str(row[1])

        if has_email_field and row[2]:
            audit_log.actor_email_snapshot = row[2]

        batch.append(audit_log)

        if len(batch) >= batch_size:
            AuditLog.objects.using(database).bulk_update(
                batch,
                ["actor_id_snapshot", "actor_email_snapshot"],
                batch_size=batch_size,
            )
            batch.clear()

    if batch:
        AuditLog.objects.using(database).bulk_update(
            batch,
            ["actor_id_snapshot", "actor_email_snapshot"],
            batch_size=batch_size,
        )


def restore_actor_ids_backward(apps, schema_editor):
    AuditLog = apps.get_model("audit", "AuditLog")
    User = apps.get_model(*settings.AUTH_USER_MODEL.split("."))
    db_alias = schema_editor.connection.alias

    batch = []

    records = (
        AuditLog.objects.using(db_alias)
        .values_list("pk", "actor_id_snapshot")
        .iterator(chunk_size=BATCH_SIZE)
    )

    for pk, actor_id_snapshot in records:
        if actor_id_snapshot:
            batch.append((pk, actor_id_snapshot))

        if len(batch) >= BATCH_SIZE:
            restore_batch(AuditLog, User, batch, db_alias)
            batch.clear()

    if batch:
        restore_batch(AuditLog, User, batch, db_alias)


def restore_batch(AuditLog, User, batch, db_alias):
    actor_ids = [actor_id for _, actor_id in batch]

    existing_ids = set(
        User.objects.using(db_alias).filter(pk__in=actor_ids).values_list("pk", flat=True)
    )

    records = [
        AuditLog(pk=pk, actor_id=actor_id) for pk, actor_id in batch if actor_id in existing_ids
    ]

    if records:
        AuditLog.objects.using(db_alias).bulk_update(
            records,
            ["actor"],
            batch_size=BATCH_SIZE,
        )


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("audit", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="auditlog",
            name="actor_id_snapshot",
            field=models.CharField(
                blank=True,
                db_index=True,
                max_length=255,
            ),
        ),
        migrations.RunPython(
            copy_actor_ids_forward,
            restore_actor_ids_backward,
        ),
        migrations.RemoveField(
            model_name="auditlog",
            name="actor",
        ),
    ]
