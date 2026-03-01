import logging
from uuid import UUID

import httpx
from fastapi import status, HTTPException

from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import async_session_factory
from app.core.rabbit_config import rabbit_broker
from app.exceptions import PRODUCT_NOT_FOUND_EXCEPTION
from app.models.orders import OrderModel, OrderStatus, OrderItemModel
from app.schemas import OrderCreateSchema

logger = logging.getLogger(__name__)


class OrderService:
    @classmethod
    async def create_order(cls, session: AsyncSession, order_data: OrderCreateSchema):
        logger.info("create_order")

        stock_response = await cls.check_products_stock(order_data)
        logger.info(f"products in stock")

        order = OrderModel(
            user_id=order_data.user_id,
            status=OrderStatus.PENDING,
            total_amount=stock_response.get("total_amount", 0),
        )
        session.add(order)
        await session.flush()

        await cls.reserve_products(order.id, order_data.order_items)

        for order_item in stock_response.get("products"):
            order_item_model = OrderItemModel(**order_item, order_id=order.id)
            session.add(order_item_model)

        await session.commit()
        return {"status": "processing", "order_id": order.id}

    @classmethod
    async def check_products_stock(
            cls,
            order_data: OrderCreateSchema,
    ) -> dict:
        logger.info("check_products_stock")

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{settings.urls.NGINX_URL}/products/stock",
                    json={"items": order_data.model_dump().get("order_items")},
                    headers={"Content-Type": "application/json"},
                )

                response.raise_for_status()
                result = response.json()
                logger.info("result: %s", result)

                if not result.get("ok"):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Products not in stock",
                    )

                return result
            except httpx.TimeoutException:
                logger.exception("Product service timeout")
                raise HTTPException(
                    status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                    detail="Product service timeout",
                )
            except httpx.HTTPStatusError as e:
                logger.exception(f"Product service error: {e.response.status_code}")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"Product service error: {e.response.status_code}",
                )
            except Exception as e:
                logger.exception(f"Unexpected error: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"Unexpected error: {str(e)}",
                )

    @classmethod
    async def reserve_products(cls, order_id: UUID, items: list):
        payload = {
            "correlation_id": str(order_id),
            "type": "reserve_products",
            "sender": "order-service",
            "items": items
        }
        await rabbit_broker.publish(payload, routing_key=settings.rabbitmq.PRODUCTS_RESERVE_ROUTING_KEY)

    @classmethod
    async def get_order_status_by_id(cls, session: AsyncSession, order_id: UUID) -> OrderStatus | None:
        stmt = select(OrderModel).where(OrderModel.id == order_id)
        result = await session.scalar(stmt)
        if not result:
            return None
        return result.status

    @classmethod
    async def move_order_to_reserved(cls, order_data: dict):
        async with async_session_factory() as session:
            order_id = order_data.get("order_id")

            order_status = await cls.get_order_status_by_id(session, order_id)
            if order_status != OrderStatus.PENDING or not order_status:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Order not pending"
                )

            stmt = (
                update(OrderModel)
                .where(
                    and_(
                        OrderModel.id == order_id,
                        OrderModel.status == OrderStatus.PENDING,
                    )
                )
                .values({"status": OrderStatus.RESERVED})
            )
            await session.execute(stmt)
            await session.commit()


    @classmethod
    async def confirm_order(cls, session: AsyncSession, order_id: UUID):
        order_status = await cls.get_order_status_by_id(session, order_id)
        if order_status != OrderStatus.RESERVED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Order not reserver"
            )

        if order_status == OrderStatus.PAID:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Order already reserved"
            )

        stmt = (
            update(OrderModel)
            .where(
                and_(
                    OrderModel.id == order_id,
                    OrderModel.status == OrderStatus.RESERVED,
                )
            )
            .values({"status": OrderStatus.PAID})
        )

        await session.execute(stmt)
        await session.commit()

        # TODO: сделать удаление из reserved_products

    @classmethod
    async def move_order_to_preparing(cls, session: AsyncSession, order_id: UUID):
        order_status = await cls.get_order_status_by_id(session, order_id)
        if order_status != OrderStatus.PAID:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Order not paid"
            )

        stmt = (
            update(OrderModel)
            .where(OrderModel.id == order_id)
            .values({"status": OrderStatus.PREPARING})
        )
        await session.execute(stmt)
        await session.commit()
        return {"ok": True}

    @classmethod
    async def get_order_by_id(cls, session: AsyncSession, order_id: UUID) -> OrderModel:
        stmt = select(OrderModel).where(OrderModel.id == order_id)
        order = await session.scalar(stmt)
        if not order:
            raise PRODUCT_NOT_FOUND_EXCEPTION
        return order

    # TODO: оптимизировать
    @classmethod
    async def has_user_purchased_product(
        cls,
        session: AsyncSession,
        user_id: UUID,
        product_id: int,
    ) -> bool:
        stmt = (
            select(OrderModel.id)
            .where(OrderModel.user_id == user_id)
        )
        order_ids = list((await session.scalars(stmt)).all())

        stmt = (
            select(OrderItemModel.product_id)
            .where(OrderItemModel.order_id.in_(order_ids))
        )
        product_ids = list((await session.scalars(stmt)).all())

        return product_id in product_ids
