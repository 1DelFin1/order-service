import logging
from collections import defaultdict
from uuid import UUID

import httpx
from fastapi import status, HTTPException

from sqlalchemy import select, update, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import async_session_factory
from app.core.rabbit_config import rabbit_broker
from app.exceptions import PRODUCT_NOT_FOUND_EXCEPTION
from app.models.orders import OrderModel, OrderStatus, OrderItemModel
from app.schemas import OrderCreateSchema

logger = logging.getLogger(__name__)


class OrderService:
    @staticmethod
    def _build_orders_payload(order_rows, item_rows) -> list[dict]:
        items_by_order_id: dict[UUID, list[dict]] = defaultdict(list)
        for item in item_rows:
            items_by_order_id[item.order_id].append(
                {
                    "product_id": item.product_id,
                    "quantity": item.quantity,
                    "price": item.price,
                    "seller_id": item.seller_id,
                }
            )

        return [
            {
                "id": order.id,
                "user_id": order.user_id,
                "status": order.status.value,
                "total_amount": order.total_amount,
                "created_at": order.created_at,
                "order_items": items_by_order_id.get(order.id, []),
            }
            for order in order_rows
        ]

    @classmethod
    async def create_order(cls, session: AsyncSession, order_data: OrderCreateSchema):
        logger.info("create_order")

        stock_response = await cls.check_products_stock(order_data)
        logger.info("products in stock")

        order = OrderModel(
            user_id=order_data.user_id,
            status=OrderStatus.PENDING,
            total_amount=stock_response.get("total_amount", 0),
        )
        session.add(order)
        await session.flush()

        await cls.reserve_products(order.id, order_data.order_items)

        for order_item in stock_response.get("products"):
            if order_item.get("seller_id"):
                order_item["seller_id"] = UUID(order_item["seller_id"])
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
                        detail="Products not in stock",
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
            "order_id": str(order_id),
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
                    detail="Order is not pending"
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
        if order_status == OrderStatus.PAID:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Order already paid"
            )

        if order_status != OrderStatus.RESERVED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Order is not reserver"
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

        await cls.move_order_to_preparing(session, order_id)

        payload = {"order_id": order_id}
        await rabbit_broker.publish(payload, routing_key=settings.rabbitmq.PRODUCTS_DELETE_ROUTING_KEY)

    @classmethod
    async def move_order_to_preparing(cls, session: AsyncSession, order_id: UUID):
        order_status = await cls.get_order_status_by_id(session, order_id)
        if order_status == OrderStatus.PREPARING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Order already prepared"
            )

        if order_status != OrderStatus.PAID:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Order not paid"
            )

        stmt = (
            update(OrderModel)
            .where(OrderModel.id == order_id)
            .values({"status": OrderStatus.PREPARING})
        )
        await session.execute(stmt)
        await session.commit()

    @classmethod
    async def get_order_by_id(cls, session: AsyncSession, order_id: UUID) -> OrderModel:
        stmt = select(OrderModel).where(OrderModel.id == order_id)
        order = await session.scalar(stmt)
        if not order:
            raise PRODUCT_NOT_FOUND_EXCEPTION
        return order

    @classmethod
    async def get_orders_by_user_id(
        cls,
        session: AsyncSession,
        user_id: UUID,
    ) -> list[dict]:
        orders_stmt = (
            select(
                OrderModel.id,
                OrderModel.user_id,
                OrderModel.status,
                OrderModel.total_amount,
                OrderModel.created_at,
            )
            .where(OrderModel.user_id == user_id)
            .order_by(OrderModel.created_at.desc())
        )
        order_rows = (await session.execute(orders_stmt)).all()

        if not order_rows:
            return []

        order_ids = [row.id for row in order_rows]
        items_stmt = (
            select(
                OrderItemModel.order_id,
                OrderItemModel.product_id,
                OrderItemModel.quantity,
                OrderItemModel.price,
                OrderItemModel.seller_id,
            )
            .where(OrderItemModel.order_id.in_(order_ids))
        )
        item_rows = (await session.execute(items_stmt)).all()

        return cls._build_orders_payload(order_rows, item_rows)

    @classmethod
    async def get_orders_by_seller_id(
        cls,
        session: AsyncSession,
        seller_id: UUID,
    ) -> list[dict]:
        order_ids_stmt = (
            select(OrderItemModel.order_id)
            .where(OrderItemModel.seller_id == seller_id)
            .distinct()
        )
        order_ids = list((await session.scalars(order_ids_stmt)).all())
        if not order_ids:
            return []

        orders_stmt = (
            select(
                OrderModel.id,
                OrderModel.user_id,
                OrderModel.status,
                OrderModel.total_amount,
                OrderModel.created_at,
            )
            .where(OrderModel.id.in_(order_ids))
            .order_by(OrderModel.created_at.desc())
        )
        order_rows = (await session.execute(orders_stmt)).all()

        items_stmt = (
            select(
                OrderItemModel.order_id,
                OrderItemModel.product_id,
                OrderItemModel.quantity,
                OrderItemModel.price,
                OrderItemModel.seller_id,
            )
            .where(
                and_(
                    OrderItemModel.order_id.in_(order_ids),
                    OrderItemModel.seller_id == seller_id,
                )
            )
        )
        item_rows = (await session.execute(items_stmt)).all()

        return cls._build_orders_payload(order_rows, item_rows)

    @classmethod
    async def get_orders_count_by_seller_id(
        cls,
        session: AsyncSession,
        seller_id: UUID,
    ) -> int:
        stmt = (
            select(func.count(func.distinct(OrderItemModel.order_id)))
            .where(OrderItemModel.seller_id == seller_id)
        )
        orders_count = await session.scalar(stmt)
        return int(orders_count or 0)

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
