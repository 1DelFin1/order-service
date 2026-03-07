import json
from abc import ABC, abstractmethod
from typing import Sequence, TypeVar

from pydantic import BaseModel
from redis.asyncio import Redis


TModel = TypeVar("TModel", bound=BaseModel)


class RedisInterface(ABC):
    @abstractmethod
    async def get_model_list(self, key: str, schema: type[TModel]) -> list[TModel]:
        raise NotImplementedError

    @abstractmethod
    async def set_model_list(self, key: str, items: Sequence[BaseModel]) -> None:
        raise NotImplementedError


class RedisStorage(RedisInterface):
    def __init__(self, client: Redis):
        self._client = client

    async def get_model_list(self, key: str, schema: type[TModel]) -> list[TModel]:
        redis_value = await self._client.get(key)
        if not redis_value:
            return []

        try:
            raw_items = json.loads(redis_value)
        except json.JSONDecodeError:
            return []

        if not isinstance(raw_items, list):
            return []

        items: list[TModel] = []
        for raw_item in raw_items:
            try:
                items.append(schema.model_validate(raw_item))
            except Exception:
                continue
        return items

    async def set_model_list(self, key: str, items: Sequence[BaseModel]) -> None:
        payload = json.dumps([item.model_dump() for item in items], ensure_ascii=False)
        await self._client.set(key, payload)
