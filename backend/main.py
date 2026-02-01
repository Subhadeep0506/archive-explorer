from typing import Optional
from dotenv import load_dotenv
import psutil

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

from src.router.auth import router as auth_router
from src.router.profile import router as profile_router
from src.router.arxiv import router as arxiv_router
from src.router.paper import router as paper_router

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
        yield
    finally:
        logger = getattr(app.state, "logger", SingletonLogger().get_logger())
        if logger:
            logger.info("Shutting down application")
        model = getattr(app.state, "model", None)
        if model and hasattr(model, "close"):
            try:
                model.close()
            except Exception:
                if logger:
                    logger.exception("Error closing model during shutdown")


app = FastAPI(
    title="The Arxiver - Backend",
    description="FastAPI backend application for The Arxiver. Supports user authentication, question answering from various Arxiv papers.",
    version="0.0.1",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security_scheme = HTTPBearer()
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
    return {"message": "Welcome to The Arxiver Backend API"}

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
