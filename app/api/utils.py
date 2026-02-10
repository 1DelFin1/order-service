import asyncio
import aiohttp

from uuid import UUID

from fastapi import HTTPException, status

from app.core.rabbit_broker import rabbit_broker
from app.schemas import OrderCreateSchema


class OrderManager:
    @classmethod
    async def reserve_products(cls, order_id: UUID):
        message = {
            "correlation_id": order_id,
            "type": "reserve_products",
            "sender": "order-service",
            "payload": {},
        }
        await rabbit_broker.publish("")
