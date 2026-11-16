from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator

from app.services.validation import find_warnings


class LineItemData(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    description: str = Field(min_length=1, max_length=200)
    quantity: float = Field(default=1, gt=0)
    unit_price: float | None = None
    amount: float


class ReceiptData(BaseModel):
    """The fields we extract from a receipt. Also used as the update payload."""

    merchant: str = Field(default="Unknown", min_length=1, max_length=120)
    purchase_date: date | None = None
    currency: str = Field(default="USD", min_length=3, max_length=3)
    subtotal: float | None = None
    tax: float | None = None
    total: float = Field(default=0, ge=0)
    payment_method: str | None = Field(default=None, max_length=40)
    category: str = Field(default="Other", max_length=40)
    items: list[LineItemData] = []

    @field_validator("currency")
    @classmethod
    def upper_case_currency(cls, value: str) -> str:
        return value.upper()


class ReceiptOut(ReceiptData):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    has_image: bool
    is_sample: bool

    @computed_field
    @property
    def warnings(self) -> list[str]:
        return find_warnings(self)


class ReceiptPage(BaseModel):
    items: list[ReceiptOut]
    total: int


class CategoryTotal(BaseModel):
    category: str
    count: int
    total: float


class Summary(BaseModel):
    receipt_count: int
    sample_count: int
    total_spent: float
    by_category: list[CategoryTotal]
