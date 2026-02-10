import aio_pika
from faststream import FastStream
from faststream.rabbit import (
    ExchangeType,
    RabbitExchange,
    RabbitQueue,
)

from app.core.rabbit_broker import rabbit_broker


app = FastStream(rabbit_broker)

orders_queue = RabbitQueue(
    name="orders-queue",
    durable=True,
)

orders_exchange = RabbitExchange(
    name="orders-exchange",
    type=ExchangeType.FANOUT,
)


@app.after_startup
async def bind_queue_exchange():
    queue: aio_pika.RobustQueue = await rabbit_broker.declare_queue(
        orders_queue,
    )

    exchange: aio_pika.RobustExchange = await rabbit_broker.declare_exchange(
        orders_exchange,
    )

    await queue.bind(
        exchange=exchange,
        routing_key=queue.name,
    )
