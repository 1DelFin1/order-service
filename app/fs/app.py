from faststream import FastStream

from app.core.config import settings
from app.core.rabbit_config import rabbit_broker, orders_reserved_queue, orders_exchange
from app.fs.routers import orders_router

app = FastStream(rabbit_broker)

rabbit_broker.include_router(orders_router)


@app.after_startup
async def after_startup():
    exchange = await rabbit_broker.declare_exchange(
        orders_exchange
    )
    queue = await rabbit_broker.declare_queue(
        orders_reserved_queue
    )

    await queue.bind(
        exchange=exchange,
        routing_key=settings.rabbitmq.ORDERS_RESERVED_ROUTING_KEY,
    )
