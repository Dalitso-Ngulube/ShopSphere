from django.apps import apps
from django.db import models

from tests.architecture.contracts import ALLOWED_DEPENDENCIES

PHASE2_TEMP_ALLOWED_EXTRA: dict[str, set[str]] = {
    "audit": {"auth"},
}


def test_no_upward_foreign_keys():
    violations: list[str] = []
    for model in apps.get_models():
        source_app = model._meta.app_label
        if source_app not in ALLOWED_DEPENDENCIES:
            continue
        allowed = (
            ALLOWED_DEPENDENCIES[source_app]
            | PHASE2_TEMP_ALLOWED_EXTRA.get(source_app, set())
            | {source_app}
        )
        for field in model._meta.get_fields():
            if isinstance(field, models.ForeignKey) and field.remote_field:
                target_app = field.remote_field.model._meta.app_label
                if target_app not in allowed:
                    target_name = field.remote_field.model.__name__
                    violations.append(
                        f"{source_app}.{model.__name__}.{field.name} -> {target_app}.{target_name}"
                    )
    assert not violations, "Disallowed foreign-key dependencies found:\n" + "\n".join(violations)
