import pytest

from app.extractors.mock_extractor import sample_receipts
from app.services.samples import seed_samples

BASE = "/api/v1/receipts"


@pytest.fixture
def seeded(client, session_factory):
    """A client whose database starts with the sample receipts."""
    with session_factory() as db:
        seed_samples(db)
    return client


def test_seeded_receipts_are_marked_as_samples(seeded):
    page = seeded.get(BASE).json()
    assert page["total"] == len(sample_receipts())
    assert all(receipt["is_sample"] for receipt in page["items"])
    assert all(receipt["items"] for receipt in page["items"])


def test_summary_counts_samples(seeded):
    assert seeded.get(f"{BASE}/summary").json()["sample_count"] == len(sample_receipts())


def test_scanned_receipt_is_not_a_sample(scanned):
    assert scanned["is_sample"] is False


def test_remove_samples_keeps_real_receipts(seeded):
    scanned = seeded.post(
        f"{BASE}/scan",
        files={"file": ("receipt.png", b"\x89PNG\r\n\x1a\n" + b"\x00" * 16, "image/png")},
    ).json()

    assert seeded.delete(f"{BASE}/samples").status_code == 204

    page = seeded.get(BASE).json()
    assert [receipt["id"] for receipt in page["items"]] == [scanned["id"]]
    assert seeded.get(f"{BASE}/summary").json()["sample_count"] == 0
