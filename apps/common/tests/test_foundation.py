import hashlib
from decimal import Decimal

import pytest
from django.utils import timezone

from apps.common.locks import LockOrderError, validate_lock_order
from apps.common.models import IdempotencyKey
from apps.common.money import round_money, to_decimal


def test_round_money_half_up_and_rejects_float():
    assert round_money("10.005") == Decimal("10.01")
    assert round_money(Decimal("2.344")) == Decimal("2.34")
    assert to_decimal("99.95") == Decimal("99.95")

    with pytest.raises(TypeError):
        to_decimal(19.99)  # type: ignore[arg-type]


def test_validate_lock_order_enforces_hierarchy():
    validate_lock_order(["user", "order", "payment", "inventory_item", "document_sequence"])

    with pytest.raises(LockOrderError):
        validate_lock_order(["payment", "order"])


def test_validate_lock_order_enforces_same_rank_type_order():
    validate_lock_order(["refund", "return_request"])

    with pytest.raises(LockOrderError):
        validate_lock_order(["return_request", "refund"])


def test_validate_lock_order_rejects_unknown_resources():
    with pytest.raises(LockOrderError):
        validate_lock_order(["unknown_resource"])


@pytest.mark.django_db
def test_idempotency_key_creation_without_user_fk():
    request_hash = hashlib.sha256(b"checkout request").hexdigest()

    record = IdempotencyKey.objects.create(
        owner_ref="usr_12345",
        scope="checkout.place_order",
        key="idem-key-001",
        request_hash=request_hash,
        response_status=201,
        response_body={"order_id": 1},
        expires_at=timezone.now() + timezone.timedelta(hours=24),
    )

    assert record.pk is not None
    assert record.request_hash == request_hash
    assert str(record) == "checkout.place_order:usr_12345:<redacted>"
    assert "idem-key-001" not in str(record)
