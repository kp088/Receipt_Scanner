"""The prompt and reply parsing shared by every AI provider."""

import json
import logging

from pydantic import ValidationError

from app.extractors.base import ExtractionError
from app.schemas import ReceiptData

logger = logging.getLogger(__name__)

PROMPT = """You are a receipt parser. Read the receipt in the image and return ONLY a JSON
object with exactly these keys:

{
  "merchant": string,
  "purchase_date": "YYYY-MM-DD" or null,
  "currency": 3-letter ISO code such as "USD",
  "subtotal": number or null,
  "tax": number or null,
  "total": number,
  "payment_method": string or null,
  "category": one of "Groceries", "Dining", "Transport", "Shopping", "Health", "Utilities", "Other",
  "items": [{"description": string, "quantity": number, "unit_price": number or null, "amount": number}]
}

Rules:
- Copy numbers exactly as printed. Never invent or "fix" a value.
- "amount" is the line total for that item.
- Use null when a value is missing or unreadable.
- If the image is not a receipt, return {"error": "not a receipt"}.
"""


def parse_model_reply(raw: str) -> ReceiptData:
    """Turn a model's raw text reply into a validated receipt."""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ExtractionError("The AI service returned invalid JSON.") from exc

    if not isinstance(data, dict) or "error" in data:
        raise ExtractionError("This image does not look like a receipt.")

    # Drop nulls so schema defaults apply (e.g. merchant -> "Unknown").
    data = {key: value for key, value in data.items() if value is not None}

    try:
        return ReceiptData.model_validate(data)
    except ValidationError as exc:
        logger.warning("Model output failed schema validation: %s", exc)
        raise ExtractionError("The AI service returned data in an unexpected shape.") from exc
