from uuid import UUID

from fastapi import APIRouter

from app.services import FavoritesService
from app.schemas import FavoriteSchema

favorites_router = APIRouter(prefix="/favorites", tags=["favorites"])


@favorites_router.get("/{user_id}")
async def get_favorites_by_user_id(
    user_id: UUID,
):
    return await FavoritesService.get(user_id)


@favorites_router.post("/{user_id}")
async def set_favorites(
    user_id: UUID,
    products: list[FavoriteSchema],
):
    await FavoritesService.set(user_id, products)
    return {"ok": True}
