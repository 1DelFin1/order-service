__all__ = ("orders_router", "cart_router", "main_router", "favorites_router")

from fastapi import APIRouter

from app.api.routers.orders import orders_router
from app.api.routers.cart import cart_router
from app.api.routers.favorites import favorites_router

main_router = APIRouter()
main_router.include_router(orders_router)
main_router.include_router(cart_router)
main_router.include_router(favorites_router)
