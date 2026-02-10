from uuid import UUID

from fastapi import APIRouter

from app.api.deps import SessionDep
from app.services import OrderService
from app.schemas import OrderCreateSchema


orders_router = APIRouter(prefix="/orders", tags=["orders"])


@orders_router.post("")
async def create_order(session: SessionDep, order_data: OrderCreateSchema):
    product = await OrderService.create_order(session, order_data)
    return product


@orders_router.get("/{order_id}")
async def get_order_by_id(session: SessionDep, order_id: UUID):
    product = await OrderService.get_order_by_id(session, order_id)
    return product


@orders_router.get("/users/{user_id}/purchased-products/{product_id}")
async def check_products_purchased(
    session: SessionDep,
    user_id: UUID,
    product_id: int,
):
    has_purchased = await OrderService.has_user_purchased_product(
        session, user_id, product_id
    )
    return {"has_purchased": has_purchased}
