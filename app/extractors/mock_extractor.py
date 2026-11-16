from datetime import date, timedelta

from app.schemas import LineItemData, ReceiptData


def _days_ago(days: int) -> date:
    return date.today() - timedelta(days=days)


def sample_receipts() -> list[ReceiptData]:
    """Example receipts, used by the mock extractor and to fill a new database."""
    return [
        ReceiptData(
            merchant="Green Basket Market",
            purchase_date=_days_ago(1),
            subtotal=23.46,
            tax=1.55,
            total=25.01,
            payment_method="Visa",
            category="Groceries",
            items=[
                LineItemData(description="Organic bananas", quantity=1, amount=2.49),
                LineItemData(description="Whole milk 1 gal", quantity=1, amount=4.29),
                LineItemData(description="Sourdough loaf", quantity=1, amount=5.99),
                LineItemData(description="Free-range eggs", quantity=2, unit_price=5.345, amount=10.69),
            ],
        ),
        ReceiptData(
            merchant="Corner Bistro",
            purchase_date=_days_ago(3),
            subtotal=41.00,
            tax=3.64,
            total=44.64,
            payment_method="Mastercard",
            category="Dining",
            items=[
                LineItemData(description="Margherita pizza", quantity=1, amount=16.00),
                LineItemData(description="Caesar salad", quantity=1, amount=11.00),
                LineItemData(description="Sparkling water", quantity=2, unit_price=3.50, amount=7.00),
                LineItemData(description="Tiramisu", quantity=1, amount=7.00),
            ],
        ),
        # This one is wrong on purpose so the validation warnings can be seen in the demo.
        ReceiptData(
            merchant="City Hardware",
            purchase_date=_days_ago(7),
            subtotal=58.97,
            tax=3.91,
            total=68.88,
            payment_method="Cash",
            category="Shopping",
            items=[
                LineItemData(description="LED bulbs 4-pack", quantity=1, amount=12.99),
                LineItemData(description="Cordless drill bit set", quantity=1, amount=29.99),
                LineItemData(description="Painter's tape", quantity=2, unit_price=5.995, amount=11.99),
            ],
        ),
        ReceiptData(
            merchant="Metro Fuel Station",
            purchase_date=_days_ago(10),
            subtotal=46.20,
            tax=3.23,
            total=49.43,
            payment_method="Visa",
            category="Transport",
            items=[
                LineItemData(description="Unleaded fuel 12 gal", quantity=12, unit_price=3.60, amount=43.20),
                LineItemData(description="Car wash", quantity=1, amount=3.00),
            ],
        ),
        ReceiptData(
            merchant="Wellness Pharmacy",
            purchase_date=_days_ago(14),
            subtotal=27.47,
            tax=1.92,
            total=29.39,
            payment_method="Debit card",
            category="Health",
            items=[
                LineItemData(description="Vitamin D tablets", quantity=1, amount=12.99),
                LineItemData(description="Bandages", quantity=1, amount=4.49),
                LineItemData(description="Hand sanitizer", quantity=2, unit_price=4.995, amount=9.99),
            ],
        ),
    ]


class MockExtractor:
    """Returns sample receipts without calling any API.

    Lets the project run with no API key, and keeps the tests free and deterministic.
    """

    def extract(self, image_bytes: bytes, content_type: str) -> ReceiptData:
        samples = sample_receipts()
        return samples[len(image_bytes) % len(samples)]
