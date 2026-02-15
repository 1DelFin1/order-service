from typing import List
from uuid import UUID

from pydantic import BaseModel


class OrderBaseSchema(BaseModel):
    product_id: int
    quantity: int


class OrderCreateSchema(BaseModel):
    user_id: UUID
    order_items: List[OrderBaseSchema]
