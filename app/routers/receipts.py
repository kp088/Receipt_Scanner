import csv
import io
import logging
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, Response, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.config import Settings, get_settings
from app.database import get_db
from app.dependencies import get_extractor
from app.extractors.base import ExtractionError, ReceiptExtractor
from app.models import LineItem, Receipt
from app.schemas import CategoryTotal, ReceiptData, ReceiptOut, ReceiptPage, Summary

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/receipts", tags=["receipts"])

EXTENSIONS = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}


def detect_image_type(data: bytes) -> str | None:
    """Identify the image by its leading bytes instead of trusting the upload header."""
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return None


def apply_data(receipt: Receipt, data: ReceiptData) -> None:
    """Copy validated fields onto the ORM object, replacing its line items."""
    for field, value in data.model_dump(exclude={"items"}).items():
        setattr(receipt, field, value)
    receipt.items = [LineItem(**item.model_dump()) for item in data.items]


def get_receipt_or_404(receipt_id: int, db: Session) -> Receipt:
    receipt = db.get(Receipt, receipt_id)
    if receipt is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Receipt not found.")
    return receipt


@router.post("/scan", response_model=ReceiptOut, status_code=status.HTTP_201_CREATED)
def scan_receipt(
    file: UploadFile,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    extractor: ReceiptExtractor = Depends(get_extractor),
):
    """Upload a receipt image, extract its data and save it."""
    max_bytes = settings.max_upload_mb * 1024 * 1024
    image = file.file.read(max_bytes + 1)

    if len(image) > max_bytes:
        raise HTTPException(
            413,  # Payload too large
            f"Image is larger than {settings.max_upload_mb} MB.",
        )

    content_type = detect_image_type(image)
    if content_type is None:
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            "Please upload a JPG, PNG or WEBP image.",
        )

    try:
        data = extractor.extract(image, content_type)
    except ExtractionError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(exc)) from exc

    # Store the image under a random name so user-supplied filenames never touch the disk.
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4().hex}{EXTENSIONS[content_type]}"
    (upload_dir / filename).write_bytes(image)

    receipt = Receipt(image_filename=filename)
    apply_data(receipt, data)
    db.add(receipt)
    db.commit()

    logger.info("Scanned receipt %s from %s", receipt.id, receipt.merchant)
    return receipt


@router.get("", response_model=ReceiptPage)
def list_receipts(
    q: str | None = Query(default=None, description="Filter by merchant name"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    query = select(Receipt)
    if q:
        query = query.where(Receipt.merchant.ilike(f"%{q}%"))

    total = db.scalar(select(func.count()).select_from(query.subquery()))
    receipts = db.scalars(
        query.options(selectinload(Receipt.items))
        .order_by(Receipt.created_at.desc(), Receipt.id.desc())
        .limit(limit)
        .offset(offset)
    ).all()
    return ReceiptPage(items=receipts, total=total)


@router.get("/summary", response_model=Summary)
def spending_summary(db: Session = Depends(get_db)):
    rows = db.execute(
        select(Receipt.category, func.count(), func.sum(Receipt.total))
        .group_by(Receipt.category)
        .order_by(func.sum(Receipt.total).desc())
    ).all()

    by_category = [
        CategoryTotal(category=category, count=count, total=round(total, 2))
        for category, count, total in rows
    ]
    sample_count = db.scalar(select(func.count()).where(Receipt.is_sample))
    return Summary(
        receipt_count=sum(row.count for row in by_category),
        sample_count=sample_count,
        total_spent=round(sum(row.total for row in by_category), 2),
        by_category=by_category,
    )


@router.get("/export.csv")
def export_csv(db: Session = Depends(get_db)):
    """Download every receipt as CSV, one row per line item."""
    receipts = db.scalars(
        select(Receipt).options(selectinload(Receipt.items)).order_by(Receipt.id)
    ).all()

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        ["receipt_id", "merchant", "purchase_date", "category", "currency",
         "item", "quantity", "amount", "receipt_total"]
    )
    for receipt in receipts:
        for item in receipt.items:
            writer.writerow(
                [receipt.id, receipt.merchant, receipt.purchase_date, receipt.category,
                 receipt.currency, item.description, item.quantity, item.amount, receipt.total]
            )

    return Response(
        buffer.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="receipts.csv"'},
    )


@router.delete("/samples", status_code=status.HTTP_204_NO_CONTENT)
def delete_samples(db: Session = Depends(get_db)):
    """Remove the sample receipts that a new database starts with."""
    for receipt in db.scalars(select(Receipt).where(Receipt.is_sample)):
        db.delete(receipt)
    db.commit()


@router.get("/{receipt_id}", response_model=ReceiptOut)
def get_receipt(receipt_id: int, db: Session = Depends(get_db)):
    return get_receipt_or_404(receipt_id, db)


@router.put("/{receipt_id}", response_model=ReceiptOut)
def update_receipt(receipt_id: int, data: ReceiptData, db: Session = Depends(get_db)):
    """Save corrections made by the user after reviewing the extraction."""
    receipt = get_receipt_or_404(receipt_id, db)
    apply_data(receipt, data)
    db.commit()
    return receipt


@router.delete("/{receipt_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_receipt(
    receipt_id: int,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    receipt = get_receipt_or_404(receipt_id, db)
    if receipt.image_filename:
        (Path(settings.upload_dir) / receipt.image_filename).unlink(missing_ok=True)
    db.delete(receipt)
    db.commit()


@router.get("/{receipt_id}/image")
def get_receipt_image(
    receipt_id: int,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    receipt = get_receipt_or_404(receipt_id, db)
    path = Path(settings.upload_dir) / (receipt.image_filename or "")
    if not receipt.image_filename or not path.is_file():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Image not found.")
    return FileResponse(path)
