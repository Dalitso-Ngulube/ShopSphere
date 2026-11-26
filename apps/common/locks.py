from collections.abc import Sequence
from contextlib import contextmanager

from django.db import OperationalError, connection, transaction

LOCK_HIERARCHY: dict[str, int] = {
    "user": 0,
    "order": 1,
    "shipment": 2,
    "payment": 3,
    "refund": 4,
    "return_request": 4,
    "coupon": 5,
    "stock_transfer": 5,
    "inventory_item": 6,
    "document_sequence": 7,
}


class LockOrderError(ValueError):
    """Raised when row locks are requested out of ADR-014 hierarchy order."""


class LockTimeoutConflict(Exception):
    """Raised when acquiring a row lock times out and should be retried."""


def validate_lock_order(lock_types: Sequence[str]) -> None:
    previous_rank = -1
    previous_type = ""

    for lock_type in lock_types:
        if lock_type not in LOCK_HIERARCHY:
            raise LockOrderError(f"Unknown lock resource type: {lock_type}")

        rank = LOCK_HIERARCHY[lock_type]

        if rank < previous_rank:
            raise LockOrderError(
                f"Lock hierarchy violation: cannot acquire '{lock_type}' "
                f"(rank {rank}) after rank {previous_rank}."
            )

        # Establish a deterministic order between different resource types
        # that share the same hierarchy rank.
        if rank == previous_rank and lock_type < previous_type:
            raise LockOrderError(
                f"Lock ordering violation: '{lock_type}' must not be acquired "
                f"after '{previous_type}' at the same hierarchy rank."
            )

        previous_rank = rank
        previous_type = lock_type


def _has_lock_timeout_sqlstate(exception: BaseException) -> bool:
    """
    PostgreSQL reports lock-not-available (including lock_timeout)
    with SQLSTATE 55P03.
    """
    current = exception

    while current is not None:
        if getattr(current, "sqlstate", None) == "55P03":
            return True

        current = current.__cause__ or current.__context__

    return False


@contextmanager
def lock_timeout(timeout_ms: int = 5000):
    """Set a local PostgreSQL lock_timeout for the current transaction."""

    if isinstance(timeout_ms, bool) or not isinstance(timeout_ms, int) or timeout_ms <= 0:
        raise ValueError("timeout_ms must be a positive integer.")

    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT set_config('lock_timeout', %s, true)",
                [f"{timeout_ms}ms"],
            )

        try:
            yield
        except OperationalError as exc:
            if _has_lock_timeout_sqlstate(exc):
                raise LockTimeoutConflict("Timed out waiting for row lock.") from exc

            raise
