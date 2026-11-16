from datetime import date, datetime, timezone

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Receipt(Base):
    __tablename__ = "receipts"

    id: Mapped[int] = mapped_column(primary_key=True)
    merchant: Mapped[str] = mapped_column(String(120), index=True)
    purchase_date: Mapped[date | None]
    currency: Mapped[str] = mapped_column(String(3))
    subtotal: Mapped[float | None]
    tax: Mapped[float | None]
    total: Mapped[float]
    payment_method: Mapped[str | None] = mapped_column(String(40))
    category: Mapped[str] = mapped_column(String(40), index=True)
    image_filename: Mapped[str | None] = mapped_column(String(80))
    is_sample: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(default=utc_now)

    items: Mapped[list["LineItem"]] = relationship(
        back_populates="receipt",
        cascade="all, delete-orphan",
        order_by="LineItem.id",
    )

    @property
    def has_image(self) -> bool:
        return bool(self.image_filename)


class LineItem(Base):
    __tablename__ = "line_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    receipt_id: Mapped[int] = mapped_column(ForeignKey("receipts.id", ondelete="CASCADE"))
    description: Mapped[str] = mapped_column(String(200))
    quantity: Mapped[float] = mapped_column(default=1)
    unit_price: Mapped[float | None]
    amount: Mapped[float]

    receipt: Mapped[Receipt] = relationship(back_populates="items")
