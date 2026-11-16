from tests.conftest import JPEG_BYTES, PNG_BYTES

BASE = "/api/v1/receipts"


def test_health(client):
    assert client.get("/api/health").json()["status"] == "ok"


def test_scan_returns_structured_receipt(scanned):
    assert scanned["id"] > 0
    assert scanned["merchant"]
    assert scanned["total"] > 0
    assert len(scanned["items"]) > 0
    assert scanned["has_image"] is True
    assert isinstance(scanned["warnings"], list)


def test_scan_rejects_non_image(client):
    response = client.post(
        f"{BASE}/scan",
        # Claims to be a PNG, but the bytes say otherwise.
        files={"file": ("notes.png", b"just some text", "image/png")},
    )
    assert response.status_code == 415


def test_scan_rejects_oversized_image(client):
    too_big = PNG_BYTES + b"\x00" * (1024 * 1024)
    response = client.post(f"{BASE}/scan", files={"file": ("big.png", too_big, "image/png")})
    assert response.status_code == 413


def test_list_supports_search_and_pagination(client, scanned):
    client.post(f"{BASE}/scan", files={"file": ("b.jpg", JPEG_BYTES, "image/jpeg")})

    page = client.get(BASE, params={"limit": 1}).json()
    assert page["total"] == 2
    assert len(page["items"]) == 1

    found = client.get(BASE, params={"q": scanned["merchant"][:5]}).json()
    assert any(r["id"] == scanned["id"] for r in found["items"])

    assert client.get(BASE, params={"q": "no-such-merchant"}).json()["total"] == 0


def test_update_saves_corrections(client, scanned):
    payload = {
        "merchant": "Corrected Store",
        "purchase_date": "2026-01-15",
        "currency": "usd",
        "subtotal": 10.0,
        "tax": 1.0,
        "total": 11.0,
        "category": "Groceries",
        "items": [{"description": "Apples", "quantity": 2, "amount": 10.0}],
    }
    response = client.put(f"{BASE}/{scanned['id']}", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["merchant"] == "Corrected Store"
    assert body["currency"] == "USD"
    assert [item["description"] for item in body["items"]] == ["Apples"]
    assert body["warnings"] == []


def test_update_rejects_invalid_data(client, scanned):
    response = client.put(f"{BASE}/{scanned['id']}", json={"merchant": "X", "total": -5})
    assert response.status_code == 422


def test_image_can_be_downloaded(client, scanned):
    response = client.get(f"{BASE}/{scanned['id']}/image")
    assert response.status_code == 200
    assert response.content == PNG_BYTES


def test_delete_removes_receipt_and_image(client, scanned):
    assert client.delete(f"{BASE}/{scanned['id']}").status_code == 204
    assert client.get(f"{BASE}/{scanned['id']}").status_code == 404
    assert client.get(f"{BASE}/{scanned['id']}/image").status_code == 404


def test_missing_receipt_returns_404(client):
    assert client.get(f"{BASE}/999").status_code == 404


def test_summary_totals_by_category(client, scanned):
    summary = client.get(f"{BASE}/summary").json()
    assert summary["receipt_count"] == 1
    assert summary["total_spent"] == scanned["total"]
    assert summary["by_category"][0]["category"] == scanned["category"]


def test_csv_export_has_one_row_per_item(client, scanned):
    response = client.get(f"{BASE}/export.csv")
    assert response.headers["content-type"].startswith("text/csv")

    lines = response.text.strip().splitlines()
    assert lines[0].startswith("receipt_id,merchant")
    assert len(lines) == 1 + len(scanned["items"])
