from django.db import migrations

FORWARD_SQL = """
CREATE OR REPLACE FUNCTION audit_reject_mutation()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION 'AuditLog records are immutable.'
        USING ERRCODE = '55000';
END;
$$;

CREATE TRIGGER audit_log_prevent_update_delete
BEFORE UPDATE OR DELETE
ON audit_auditlog
FOR EACH ROW
EXECUTE FUNCTION audit_reject_mutation();

CREATE TRIGGER audit_log_prevent_truncate
BEFORE TRUNCATE
ON audit_auditlog
FOR EACH STATEMENT
EXECUTE FUNCTION audit_reject_mutation();
"""


REVERSE_SQL = """
DROP TRIGGER IF EXISTS audit_log_prevent_truncate
ON audit_auditlog;

DROP TRIGGER IF EXISTS audit_log_prevent_update_delete
ON audit_auditlog;

DROP FUNCTION IF EXISTS audit_reject_mutation();
"""


class Migration(migrations.Migration):
    dependencies = [
        ("audit", "0002_remove_auditlog_actor_auditlog_actor_id_snapshot"),
    ]

    operations = [
        migrations.RunSQL(
            sql=FORWARD_SQL,
            reverse_sql=REVERSE_SQL,
        ),
    ]
