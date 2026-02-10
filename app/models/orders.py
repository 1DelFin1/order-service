from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import Integer, Float, DECIMAL
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import TimestampMixin


class OrderStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    CONFIRMED = "confirmed"
    PAYMENT_FAILED = "payment_failed"
    OUT_OF_STOCK = "out_of_stock"
    PREPARING = "preparing"
    SHIPPING = "shipping"
    IN_TRANSIT = "in_transit"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"
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
