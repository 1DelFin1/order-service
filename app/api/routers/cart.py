from uuid import UUID

from fastapi import APIRouter

from app.services import CartService
from app.schemas import CartSchema

cart_router = APIRouter(prefix="/cart", tags=["cart"])


@cart_router.get("/{user_id}")
async def get_cart_by_user_id(
    user_id: UUID,
):
    return await CartService.get(user_id)


@cart_router.post("/{user_id}")
async def set_cart(
    user_id: UUID,
    products: list[CartSchema],
):
    await CartService.set(user_id, products)
    return {"ok": True}
