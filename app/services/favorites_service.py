from uuid import UUID

from app.core.redis_client import redis_storage
from app.schemas import FavoriteSchema


class FavoritesService:
    FAVORITES_KEY_PREFIX = "favorites"

    @classmethod
    def _build_key(cls, user_id: UUID) -> str:
        return f"{cls.FAVORITES_KEY_PREFIX}:{user_id}"

    @classmethod
    async def get(cls, user_id: UUID) -> list[FavoriteSchema]:
        return await redis_storage.get_model_list(cls._build_key(user_id), FavoriteSchema)

    @classmethod
    async def set(cls, user_id: UUID, products: list[FavoriteSchema]) -> None:
        await redis_storage.set_model_list(cls._build_key(user_id), products)
