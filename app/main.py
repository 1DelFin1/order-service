from contextlib import asynccontextmanager

import uvicorn

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import orders_router
from app.core.rabbit_broker import rabbit_broker
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    await rabbit_broker.start()
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
