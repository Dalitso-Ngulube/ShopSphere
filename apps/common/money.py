from decimal import ROUND_HALF_UP, Decimal
from typing import Final

TWO_PLACES: Final[Decimal] = Decimal("0.01")


def to_decimal(value: Decimal | int | str) -> Decimal:
    """Convert numeric inputs to Decimal without binary float precision loss."""
    if isinstance(value, float):
        raise TypeError(
            "Float values are prohibited for monetary calculations; pass Decimal, int, or str."
        )
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def round_money(value: Decimal | int | str) -> Decimal:
    """Round monetary amounts to 2 decimal places using ROUND_HALF_UP (BR-5)."""
    return to_decimal(value).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
