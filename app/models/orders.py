from enum import Enum
from uuid import uuid4, UUID

from sqlalchemy import Integer, Float
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import TimestampMixin


class OrderStatus(str, Enum):
    PENDING = "pending"
    RESERVED = "reserved"
    RESERVATION_FAILED = "reservation_failed"
    PAID = "paid"
    PAYMENT_FAILED = "payment_failed"
    PREPARING = "preparing"
    SHIPPING = "shipping"
    DELIVERED = "delivered"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class OrderModel(Base, TimestampMixin):
    __tablename__ = "orders"

    id: Mapped[UUID] = mapped_column(default=uuid4, primary_key=True)
    user_id: Mapped[UUID] = mapped_column(default=uuid4, nullable=False)
    status: Mapped[OrderStatus] = mapped_column(
        default=OrderStatus.PENDING, nullable=False
    )
    total_amount: Mapped[float] = mapped_column(Float)


class OrderItemModel(Base, TimestampMixin):
    __tablename__ = "order_items"

    id: Mapped[UUID] = mapped_column(default=uuid4, primary_key=True)
    order_id: Mapped[UUID] = mapped_column(default=uuid4, nullable=False)
    product_id: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=True)
