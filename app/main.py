from contextlib import asynccontextmanager

import uvicorn
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import orders_router
from app.core.rabbit_config import rabbit_broker, orders_queue, orders_exchange
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.basicConfig(level=logging.INFO)

    await rabbit_broker.start()

    exchange = await rabbit_broker.declare_exchange(
        orders_exchange
    )
    queue = await rabbit_broker.declare_queue(
        orders_queue
    )

    await queue.bind(exchange=exchange, routing_key="orders")
    yield
    await rabbit_broker.stop()


app = FastAPI(title="order-service", lifespan=lifespan)
app.include_router(orders_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=settings.cors.CORS_METHODS,
    allow_headers=settings.cors.CORS_HEADERS,
)

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8001, reload=True)
