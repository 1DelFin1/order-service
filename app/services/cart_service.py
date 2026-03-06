import json
from uuid import UUID

from app.core.redis_client import redis_client
from app.schemas import CartSchema


class CartService:
    CART_KEY_PREFIX = "cart"

    @classmethod
    def _build_key(cls, user_id: UUID) -> str:
        return f"{cls.CART_KEY_PREFIX}:{user_id}"

    @classmethod
    async def get(cls, user_id: UUID) -> list[CartSchema]:
        redis_value = await redis_client.get(cls._build_key(user_id))
        if not redis_value:
            return []

        try:
            raw_items = json.loads(redis_value)
        except json.JSONDecodeError:
            return []

        if not isinstance(raw_items, list):
            return []

        items: list[CartSchema] = []
        for raw_item in raw_items:
            try:
                items.append(CartSchema.model_validate(raw_item))
            except Exception:
                continue
        return items

    @classmethod
    async def set(cls, user_id: UUID, products: list[CartSchema]) -> None:
        payload = json.dumps([product.model_dump() for product in products], ensure_ascii=False)
        await redis_client.set(cls._build_key(user_id), payload)
