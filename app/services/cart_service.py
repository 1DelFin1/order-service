from uuid import UUID

from app.core.redis_client import redis_storage
from app.schemas import CartSchema


class CartService:
    CART_KEY_PREFIX = "cart"

    @classmethod
    def _build_key(cls, user_id: UUID) -> str:
        return f"{cls.CART_KEY_PREFIX}:{user_id}"

    @classmethod
    async def get(cls, user_id: UUID) -> list[CartSchema]:
        return await redis_storage.get_model_list(cls._build_key(user_id), CartSchema)

    @classmethod
    async def set(cls, user_id: UUID, products: list[CartSchema]) -> None:
        await redis_storage.set_model_list(cls._build_key(user_id), products)
