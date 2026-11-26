from django.contrib.postgres.operations import BtreeGistExtension, TrigramExtension
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        BtreeGistExtension(),
        TrigramExtension(),
        migrations.CreateModel(
            name="IdempotencyKey",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("owner_ref", models.CharField(max_length=128)),
                ("scope", models.CharField(max_length=64)),
                ("key", models.CharField(max_length=128)),
                ("request_hash", models.CharField(max_length=64)),
                ("response_status", models.PositiveSmallIntegerField()),
                ("response_body", models.JSONField()),
                ("expires_at", models.DateTimeField(db_index=True)),
            ],
            options={
                "constraints": [
                    models.UniqueConstraint(
                        fields=("owner_ref", "scope", "key"),
                        name="uq_idempotency_owner_scope_key",
                    ),
                ],
            },
        ),
    ]
