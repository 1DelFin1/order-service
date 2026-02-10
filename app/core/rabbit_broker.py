from faststream.rabbit import RabbitBroker

from app.core.config import settings


rabbit_broker = RabbitBroker(settings.rabbitmq.RABBITMQ_URL)
