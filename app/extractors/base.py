from typing import Protocol

from app.schemas import ReceiptData


class ExtractionError(Exception):
    """Raised when a receipt image cannot be turned into structured data."""


class ReceiptExtractor(Protocol):
    """Anything that can read a receipt image. Add a new provider by implementing this."""

    def extract(self, image_bytes: bytes, content_type: str) -> ReceiptData: ...
