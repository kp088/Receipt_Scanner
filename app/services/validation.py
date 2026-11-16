"""Sanity checks on extracted receipts.

LLMs misread digits now and then, so we never trust the numbers blindly.
These checks flag receipts whose figures do not add up so a person can review them.
"""

from datetime import date

# Allow a couple of cents of rounding drift.
TOLERANCE = 0.02


def _differs(a: float, b: float) -> bool:
    return abs(a - b) > TOLERANCE


def find_warnings(receipt) -> list[str]:
    """Return human-readable problems found in a receipt (empty list if none).

    Accepts any object with the receipt fields: a Pydantic schema or an ORM model.
    """
    warnings: list[str] = []
    items_sum = round(sum(item.amount for item in receipt.items), 2)
    tax = receipt.tax or 0

    if not receipt.items:
        warnings.append("No line items were found.")
    elif receipt.subtotal is not None:
        if _differs(items_sum, receipt.subtotal):
            warnings.append(
                f"Line items add up to {items_sum:.2f} but the subtotal is {receipt.subtotal:.2f}."
            )
    elif _differs(items_sum + tax, receipt.total):
        warnings.append(
            f"Line items plus tax come to {items_sum + tax:.2f} but the total is {receipt.total:.2f}."
        )

    if receipt.subtotal is not None and _differs(receipt.subtotal + tax, receipt.total):
        warnings.append(
            f"Subtotal plus tax comes to {receipt.subtotal + tax:.2f} but the total is {receipt.total:.2f}."
        )

    if receipt.total == 0:
        warnings.append("The total is zero.")

    if receipt.purchase_date is None:
        warnings.append("The purchase date could not be read.")
    elif receipt.purchase_date > date.today():
        warnings.append("The purchase date is in the future.")

    return warnings
