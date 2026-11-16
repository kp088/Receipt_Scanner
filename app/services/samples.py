"""Sample receipts shown on first run, so the dashboard is not empty."""

from sqlalchemy.orm import Session

from app.extractors.mock_extractor import sample_receipts
from app.models import LineItem, Receipt


def seed_samples(db: Session) -> int:
    """Add the sample receipts, marked as samples so they are easy to remove later."""
    samples = sample_receipts()
    # Oldest first, so the most recent purchase ends up at the top of the history.
    for data in reversed(samples):
        receipt = Receipt(is_sample=True, **data.model_dump(exclude={"items"}))
        receipt.items = [LineItem(**item.model_dump()) for item in data.items]
        db.add(receipt)
    db.commit()
    return len(samples)
