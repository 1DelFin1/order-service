from faststream.rabbit import RabbitExchange, RabbitQueue, ExchangeType, RabbitBroker

from app.core.config import settings

rabbit_broker = RabbitBroker(settings.rabbitmq.RABBITMQ_URL)

orders_exchange = RabbitExchange(
    name="orders-exchange",
    type=ExchangeType.DIRECT,
    durable=True,
)

orders_queue = RabbitQueue(
    name="orders-queue",
    durable=True,
)
