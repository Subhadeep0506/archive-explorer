import asyncio
import os
import sys
import types
import uuid
from pathlib import Path

import pytest
import psutil
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault(
    "ENCRYPTION_KEY", "MDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDA="
)

fake_supabase_module = types.ModuleType("src.core.storage.supabase")


class _FakeSupabaseStorage:
    @classmethod
    def from_env(cls):
        return cls()

    async def upload_pdf(self, file, user_id, prefix):
        return f"{prefix}/{user_id}/test.pdf"

    def get_file_url(self, key):
        return f"https://storage.example/{key}"


fake_supabase_module.SupabaseStorage = _FakeSupabaseStorage
sys.modules.setdefault("src.core.storage.supabase", fake_supabase_module)

fake_ingestion_module = types.ModuleType("src.core.ingest_engine.ingestion")


class _FakeIngestionEngine:
    @staticmethod
    async def delete_paper_using_paper_ids(arxiv_ids):
        return None


fake_ingestion_module.IngestionEngine = _FakeIngestionEngine
sys.modules.setdefault("src.core.ingest_engine.ingestion", fake_ingestion_module)

from src.database.db import Base, session_pool
from src.lib.auth import create_access_token, create_refresh_token, hash_password
from src.lib.enum import PaperSourceEnum, ServiceType
from src.errors import DatabaseConnectionError
from src.model import (
    LoginSession,
    Paper,
    Profile,
    ResourceCatalog,
    ServiceCatalog,
    Usability,
    User,
    UserSettings,
)
from src.router.auth import router as auth_router
from src.router.paper import router as paper_router
from src.router.summary import router as summary_router
from src.router.user_settings import router as user_settings_router


def run_async(awaitable):
    return asyncio.run(awaitable)


def _quote(identifier: str) -> str:
    return f'"{identifier}"'


@pytest.fixture(scope="session")
def test_database_url():
    database_url = os.getenv("TEST_DATABASE_URL") or os.getenv("DATABASE_URL")
    if not database_url:
        pytest.skip("Set TEST_DATABASE_URL or DATABASE_URL before running backend tests.")
    return database_url.strip().strip('"')


@pytest.fixture(scope="session")
def test_schema_name():
    return f"pytest_{uuid.uuid4().hex}"


@pytest.fixture(scope="session")
def test_engine(test_database_url, test_schema_name):
    async def _setup():
        admin_engine = create_async_engine(
            test_database_url,
            poolclass=NullPool,
            pool_pre_ping=True,
        )
        async with admin_engine.begin() as conn:
            await conn.execute(
                text(f"CREATE SCHEMA IF NOT EXISTS {_quote(test_schema_name)}")
            )

        engine = create_async_engine(
            test_database_url,
            poolclass=NullPool,
            pool_pre_ping=True,
            connect_args={"server_settings": {"search_path": test_schema_name}},
        )
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        return admin_engine, engine

    original_bind = session_pool.kw.get("bind")
    admin_engine, engine = run_async(_setup())
    session_pool.configure(bind=engine)

    yield engine

    async def _teardown():
        await engine.dispose()
        async with admin_engine.begin() as conn:
            await conn.execute(
                text(f"DROP SCHEMA IF EXISTS {_quote(test_schema_name)} CASCADE")
            )
        await admin_engine.dispose()

    session_pool.configure(bind=original_bind)
    run_async(_teardown())


@pytest.fixture(autouse=True)
def reset_database(test_engine):
    async def _reset():
        async with test_engine.begin() as conn:
            for table in reversed(Base.metadata.sorted_tables):
                await conn.execute(
                    text(
                        f"TRUNCATE TABLE {_quote(table.name)} RESTART IDENTITY CASCADE"
                    )
                )

    run_async(_reset())


@pytest.fixture()
def app():
    app = FastAPI()
    app.state.logger = None

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])
    app.include_router(paper_router, prefix="/api/v1/papers", tags=["Papers"])
    app.include_router(summary_router, prefix="/api/v1/summary", tags=["Summary"])
    app.include_router(
        user_settings_router, prefix="/api/v1/settings", tags=["User Settings"]
    )

    @app.get("/health")
    def health_check():
        return {
            "health": "ok",
            "cpu_usage": psutil.cpu_percent(interval=None),
            "memory_usage": psutil.virtual_memory().percent,
            "num_threads": psutil.cpu_count(),
        }

    @app.get("/")
    def root():
        return {"message": "Welcome to The Arxplorer Backend API"}

    @app.exception_handler(DatabaseConnectionError)
    async def db_connection_exception_handler(request, exc: DatabaseConnectionError):
        return JSONResponse(
            status_code=503,
            content={
                "detail": "Database connection error. Please try again later.",
                "error": str(exc),
            },
        )

    return app


@pytest.fixture()
def client(app):
    test_client = TestClient(app)
    try:
        yield test_client
    finally:
        test_client.close()


@pytest.fixture()
def external_service_spies(monkeypatch):
    calls = {
        "thumbnails": [],
        "background_index": [],
        "cleanup": [],
        "summaries": [],
        "usability": [],
    }

    async def fake_thumbnail(pdf_url: str, user_id: int, target_width: int = 400):
        calls["thumbnails"].append(
            {"pdf_url": pdf_url, "user_id": user_id, "target_width": target_width}
        )
        return f"https://thumbs.example/{user_id}.png"

    async def fake_cleanup(arxiv_ids: list[str]):
        calls["cleanup"].append(list(arxiv_ids))

    async def fake_summary(arxiv_id=None, pdf_url=None, request=None):
        calls["summaries"].append({"arxiv_id": arxiv_id, "pdf_url": pdf_url})
        target = arxiv_id or pdf_url
        return f"summary for {target}"

    async def fake_usability(arxiv_id=None, pdf_url=None, request=None):
        calls["usability"].append({"arxiv_id": arxiv_id, "pdf_url": pdf_url})
        return {
            "domain_applicability": {"Technology": 0.9},
            "reproducibility_score": {"Reproducible": 0.8},
            "new_tech_applicability": {"Agentic AI": 0.7},
            "impact_score": 0.6,
        }

    def fake_index_background(paper_id: int, title: str, abstract: str):
        calls["background_index"].append(
            {"paper_id": paper_id, "title": title, "abstract": abstract}
        )

    monkeypatch.setattr(
        "src.controller.paper.generate_first_page_thumbnail", fake_thumbnail
    )
    monkeypatch.setattr(
        "src.controller.paper.IngestionEngine.delete_paper_using_paper_ids",
        fake_cleanup,
    )
    monkeypatch.setattr("src.controller.paper.index_paper_background", fake_index_background)
    monkeypatch.setattr(
        "src.controller.summary.SummaryEngine.generate_paper_summary", fake_summary
    )
    monkeypatch.setattr(
        "src.controller.summary.UsabilityEngine.generate_paper_summary",
        fake_usability,
    )

    return calls


@pytest.fixture()
def create_user():
    def factory(
        *,
        email: str | None = None,
        username: str | None = None,
        password: str = "Password123!",
        full_name: str = "Test User",
        with_profile: bool = False,
        with_settings: bool = False,
    ):
        async def _create():
            unique_suffix = uuid.uuid4().hex[:8]
            user = User(
                username=username or f"user_{unique_suffix}",
                full_name=full_name,
                email=email or f"{unique_suffix}@example.com",
                password=hash_password(password),
            )
            async with session_pool() as session:
                session.add(user)
                await session.commit()
                await session.refresh(user)

                if with_profile:
                    session.add(Profile(user_id=user.id))
                if with_settings:
                    session.add(UserSettings(user_id=user.id))
                if with_profile or with_settings:
                    await session.commit()

                return {
                    "id": user.id,
                    "email": user.email,
                    "username": user.username,
                    "password": password,
                    "full_name": user.full_name,
                }

        return run_async(_create())

    return factory


@pytest.fixture()
def create_authenticated_user(create_user):
    def factory(
        *,
        email: str | None = None,
        username: str | None = None,
        password: str = "Password123!",
        full_name: str = "Authenticated User",
        with_profile: bool = False,
        with_settings: bool = False,
    ):
        user = create_user(
            email=email,
            username=username,
            password=password,
            full_name=full_name,
            with_profile=with_profile,
            with_settings=with_settings,
        )

        async def _create_session():
            access_token, access_expires_at = create_access_token(
                data={"sub": str(user["id"])}
            )
            refresh_token, _ = create_refresh_token(subject=str(user["id"]))
            login_session = LoginSession(
                user_id=user["id"],
                login_method="password",
                is_active=True,
                access_token=access_token,
                refresh_token=refresh_token,
                token_expires_at=access_expires_at,
                device_info="pytest",
                ip_address="127.0.0.1",
                user_agent="pytest",
            )

            async with session_pool() as session:
                session.add(login_session)
                await session.commit()
                await session.refresh(login_session)

            return {
                **user,
                "access_token": access_token,
                "refresh_token": refresh_token,
                "session_id": login_session.id,
                "headers": {"Authorization": f"Bearer {access_token}"},
            }

        return run_async(_create_session())

    return factory


@pytest.fixture()
def create_paper_record():
    def factory(
        *,
        user_id: int,
        title: str = "Paper Title",
        abstract: str = "Paper abstract",
        authors: str = "Author One",
        arxiv_id: str | None = None,
        paper_summary: str | None = "",
        pdf_url: str | None = "https://example.com/paper.pdf",
    ):
        async def _create():
            paper = Paper(
                user_id=user_id,
                title=title,
                abstract=abstract,
                authors=authors,
                arxiv_id=arxiv_id or f"{uuid.uuid4().hex[:6]}.1234",
                pdf_url=pdf_url,
                paper_summary=paper_summary,
                paper_source=PaperSourceEnum.ARXIV.value,
            )
            async with session_pool() as session:
                session.add(paper)
                await session.commit()
                await session.refresh(paper)
                return {
                    "id": paper.id,
                    "arxiv_id": paper.arxiv_id,
                    "title": paper.title,
                    "paper_summary": paper.paper_summary,
                }

        return run_async(_create())

    return factory


@pytest.fixture()
def create_usability_record():
    def factory(
        *,
        user_id: int,
        paper_id: int,
        domain_applicability: dict | None = None,
        reproducibility_score: dict | None = None,
        new_tech_applicability: dict | None = None,
        impact_score: float = 0.5,
    ):
        async def _create():
            usability = Usability(
                user_id=user_id,
                paper_id=paper_id,
                domain_applicability=domain_applicability or {"Technology": 0.8},
                reproducibility_score=reproducibility_score
                or {"Reproducible": 0.7},
                new_tech_applicability=new_tech_applicability
                or {"Agentic AI": 0.6},
                impact_score=impact_score,
            )
            async with session_pool() as session:
                session.add(usability)
                await session.commit()
                await session.refresh(usability)
                return {"id": usability.id, "impact_score": usability.impact_score}

        return run_async(_create())

    return factory


@pytest.fixture()
def seed_catalog():
    def factory():
        async def _seed():
            service_active = ServiceCatalog(
                name="OpenAI",
                slug="openai",
                service_type=ServiceType.LLM,
                description="Primary LLM provider",
                is_active=True,
            )
            service_inactive = ServiceCatalog(
                name="Disabled Service",
                slug="disabled-service",
                service_type=ServiceType.WEB_SEARCH,
                description="Inactive service",
                is_active=False,
            )

            async with session_pool() as session:
                session.add_all([service_active, service_inactive])
                await session.commit()
                await session.refresh(service_active)
                await session.refresh(service_inactive)

                resource_active = ResourceCatalog(
                    name="GPT-4.1",
                    slug="gpt-4.1",
                    service_id=service_active.id,
                    description="Active model",
                    is_active=True,
                )
                resource_inactive = ResourceCatalog(
                    name="Inactive Model",
                    slug="inactive-model",
                    service_id=service_active.id,
                    description="Inactive model",
                    is_active=False,
                )
                session.add_all([resource_active, resource_inactive])
                await session.commit()

                return {
                    "service_id": service_active.id,
                    "resource_slug": resource_active.slug,
                }

        return run_async(_seed())

    return factory
