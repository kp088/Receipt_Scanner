from datetime import date, timedelta

import pytest

from app.extractors.base import ExtractionError
from app.extractors.gemini_extractor import GeminiExtractor
from app.extractors.prompt import parse_model_reply
from app.schemas import LineItemData, ReceiptData
from app.services.validation import find_warnings


def make_receipt(**overrides) -> ReceiptData:
    fields = {
        "merchant": "Test Store",
        "purchase_date": date.today(),
        "subtotal": 10.0,
        "tax": 0.8,
        "total": 10.8,
        "items": [
            LineItemData(description="A", amount=4.0),
            LineItemData(description="B", amount=6.0),
        ],
    }
    return ReceiptData(**(fields | overrides))


def test_consistent_receipt_has_no_warnings():
    assert find_warnings(make_receipt()) == []


def test_rounding_drift_is_tolerated():
    assert find_warnings(make_receipt(total=10.81)) == []


def test_items_not_matching_subtotal_is_flagged():
    warnings = find_warnings(make_receipt(subtotal=12.0, total=12.8))
    assert any("subtotal" in w for w in warnings)


def test_subtotal_plus_tax_not_matching_total_is_flagged():
    warnings = find_warnings(make_receipt(total=20.0))
    assert any("total is 20.00" in w for w in warnings)


def test_items_checked_against_total_when_subtotal_missing():
    assert find_warnings(make_receipt(subtotal=None)) == []
    assert find_warnings(make_receipt(subtotal=None, total=50.0)) != []


def test_missing_items_and_date_are_flagged():
    warnings = find_warnings(make_receipt(items=[], purchase_date=None))
    assert any("No line items" in w for w in warnings)
    assert any("date" in w for w in warnings)


def test_future_date_is_flagged():
    tomorrow = date.today() + timedelta(days=1)
    assert any("future" in w for w in find_warnings(make_receipt(purchase_date=tomorrow)))


# --- Parsing of the model's raw reply (no network involved) ---


def test_parse_accepts_valid_json_and_fills_defaults():
    raw = '{"merchant": null, "total": 5.5, "currency": "eur", "items": []}'
    receipt = parse_model_reply(raw)
    assert receipt.merchant == "Unknown"
    assert receipt.currency == "EUR"
    assert receipt.total == 5.5


@pytest.mark.parametrize(
    "raw",
    [
        "not json at all",
        '{"error": "not a receipt"}',
        '{"total": "twelve dollars"}',
        "[1, 2, 3]",
    ],
)
def test_parse_rejects_bad_replies(raw):
    with pytest.raises(ExtractionError):
        parse_model_reply(raw)


def test_gemini_reply_text_is_joined_from_parts():
    reply = {"candidates": [{"content": {"parts": [{"text": '{"total"'}, {"text": ": 3}"}]}}]}
    assert GeminiExtractor._reply_text(reply) == '{"total": 3}'


def test_gemini_reply_without_candidates_is_an_error():
    with pytest.raises(ExtractionError):
        GeminiExtractor._reply_text({"promptFeedback": {"blockReason": "OTHER"}})
