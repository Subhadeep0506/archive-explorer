import asyncio
from typing import Optional
from dotenv import load_dotenv
import psutil
import os

load_dotenv()

from fastapi.responses import JSONResponse
import logfire

from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager
from fastapi.security import HTTPBearer
from src.database.db import Base, engine
from src.errors import DatabaseConnectionError
from src.core.logger import SingletonLogger
from fastapi.middleware.cors import CORSMiddleware
from src.core.chat_engine.query import ChatEngine
from src.core.chat_engine.agent_state import AgentState
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from src.lib.qdrant import ensure_collections_exist
from src.core.catalog_engine.update import run_daily_catalog_update
from src.router.auth import router as auth_router
from src.router.profile import router as profile_router
from src.router.arxiv import router as arxiv_router
from src.router.paper import router as paper_router
from src.router.ingestion import router as ingestion_router
from src.router.summary import router as summary_router
from src.router.chat import router as chat_router
from src.router.message import router as message_router
from src.router.session import router as session_router
from src.router.admin import router as admin_router
from src.router.user_settings import router as user_settings_router

from src.model import *

app = FastAPI()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan handler to initialize app state, create DB tables and shutdown cleanup."""
    logger = SingletonLogger().get_logger()

    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as e:
        try:
            logger = app.state.logger
        except Exception:
            logger = SingletonLogger().get_logger()
        logger.error(f"Error creating database tables: {e}")
        raise

    try:
        await asyncio.to_thread(ensure_collections_exist)
        logger.info("Qdrant collections verified.")
    except Exception as e:
        logger.warning(f"Qdrant collection setup failed (non-fatal): {e}")

    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(
        run_daily_catalog_update,
        "cron",
        hour=2,
        minute=0,
        misfire_grace_time=3600,
        max_instances=1,
        replace_existing=True,
        id="daily_catalog_update",
    )
    scheduler.start()
    logger.info("APScheduler started with daily catalog update at 02:00 UTC.")

    try:
        # Build and compile the graph
        app.state.graph = await ChatEngine.build_graph()
        logger.info("Chat engine graph successfully built and initialized.")
        yield
        logger.info("Shutting down application")

    except Exception as e:
        logger.error(f"Error during application startup: {e}")
        raise
    finally:
        scheduler.shutdown(wait=False)
        logger.info("APScheduler shut down.")


app = FastAPI(
    title="The Arxplorer - Backend",
    description="FastAPI backend application for The Arxplorer. Supports user authentication, question answering from various Arxiv papers.",
    version="0.0.1",
    lifespan=lifespan,
)
security_scheme = HTTPBearer()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.openapi_components = {
    "securitySchemes": {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }
}
app.openapi_security = [{"BearerAuth": []}]
logfire.instrument_fastapi(app, capture_headers=True)
logfire.instrument_sqlalchemy(engine)
logfire.instrument_httpx()
logfire.instrument_requests()
logfire.instrument_system_metrics(base="full")


app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(profile_router, prefix="/api/v1/profile", tags=["Profile"])
app.include_router(arxiv_router, prefix="/api/v1/arxiv", tags=["Arxiv"])
app.include_router(paper_router, prefix="/api/v1/papers", tags=["Papers"])
app.include_router(ingestion_router, prefix="/api/v1/ingestion", tags=["Ingestion"])
app.include_router(summary_router, prefix="/api/v1/summary", tags=["Summary"])
app.include_router(chat_router, prefix="/api/v1/chat", tags=["Chat"])
app.include_router(message_router, prefix="/api/v1/messages", tags=["Messages"])
app.include_router(session_router, prefix="/api/v1/sessions", tags=["Sessions"])
app.include_router(
    user_settings_router, prefix="/api/v1/settings", tags=["User Settings"]
)
app.include_router(admin_router, prefix="/admin", tags=["Admin"])


@app.get("/health")
def health_check():
    cpu_usage: Optional[float] = psutil.cpu_percent(interval=None)  # Non-blocking
    memory_usage: Optional[float] = psutil.virtual_memory().percent
    num_threads: Optional[int] = psutil.cpu_count()

    return {
        "health": "ok",
        "cpu_usage": cpu_usage,
        "memory_usage": memory_usage,
        "num_threads": num_threads,
    }


@app.get("/")
def root():
    return {"message": "Welcome to The Arxplorer Backend API"}


@app.exception_handler(DatabaseConnectionError)
async def db_connection_exception_handler(request, exc: DatabaseConnectionError):
    logger = getattr(request.app.state, "logger", SingletonLogger().get_logger())
    logger.error("Database connection error: %s", exc)
    return JSONResponse(
        status_code=503,
        content={
            "detail": "Database connection error. Please try again later.",
            "error": str(exc),
        },
    )
