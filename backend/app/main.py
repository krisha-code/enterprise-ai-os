from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.routing import APIRoute

from app.middleware.logging import logging_middleware
from app.api.router import api_router
from app.api.rag import router as rag_router
from app.config.settings import settings
from app.core.logging import setup_logging
from app.core.exceptions import register_exception_handlers
from app import models
from app.api.conversations import router as conversations_router
from app.api.messages import router as messages_router
from app.api.chat import router as chat_router

logger = setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application started successfully")
    yield
    logger.info("Application stopped")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

register_exception_handlers(app)

app.middleware("http")(logging_middleware)

app.include_router(api_router)
app.include_router(rag_router)
app.include_router(conversations_router)
app.include_router(messages_router)
app.include_router(chat_router)
for route in app.routes:
    if isinstance(route, APIRoute):
        print(route.methods, route.path)

print("=" * 50)


@app.get("/")
def root():
    return {"message": settings.APP_NAME}
