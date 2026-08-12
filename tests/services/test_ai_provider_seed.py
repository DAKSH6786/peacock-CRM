from __future__ import annotations

import importlib.util
import os
from pathlib import Path

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker

from db_models import AiProvider, AiProviderModel, GenerativeEngine
from db_models.generative_engine_seed import GENERATIVE_ENGINE_SEEDS
from db_models.provider_seed import REQUIRED_PROVIDER_CODES, SUPPORTED_AI_PROVIDERS

ROOT = Path(__file__).resolve().parents[2]


def _database_url() -> str:
    return os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://peacock:peacock@localhost:5432/peacock_one",
    )


def _can_connect() -> bool:
    try:
        engine = create_engine(_database_url())
        with engine.connect() as conn:
            conn.exec_driver_sql("SELECT 1")
        return True
    except Exception:  # noqa: BLE001
        return False


def _load_seed_module():
    spec = importlib.util.spec_from_file_location(
        "seed_dev",
        ROOT / "infra" / "scripts" / "seed_dev.py",
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.skipif(not _can_connect(), reason="PostgreSQL not available")
def test_seed_ai_providers_persist_five_rows() -> None:
    seed_dev = _load_seed_module()
    engine = create_engine(_database_url())
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    db = SessionLocal()
    try:
        seed_dev.seed_ai_providers(db)
        db.commit()

        codes = set(db.scalars(select(AiProvider.code)).all())
        assert codes >= REQUIRED_PROVIDER_CODES

        for provider in SUPPORTED_AI_PROVIDERS:
            row = db.scalar(select(AiProvider).where(AiProvider.code == provider.code))
            assert row is not None
            assert row.name == provider.name
            model_codes = {
                m.model_code
                for m in db.scalars(
                    select(AiProviderModel).where(AiProviderModel.provider_id == row.id)
                ).all()
            }
            assert {m.model_code for m in provider.models} <= model_codes

        count_before = db.scalar(select(func.count()).select_from(AiProvider))
        seed_dev.seed_ai_providers(db)
        db.commit()
        count_after = db.scalar(select(func.count()).select_from(AiProvider))
        assert count_after == count_before
        assert set(db.scalars(select(AiProvider.code)).all()) == codes
    finally:
        db.close()


@pytest.mark.skipif(not _can_connect(), reason="PostgreSQL not available")
def test_seed_generative_engines_link_to_providers() -> None:
    seed_dev = _load_seed_module()
    engine = create_engine(_database_url())
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    db = SessionLocal()
    try:
        seed_dev.seed_ai_providers(db)
        seed_dev.seed_generative_engines(db)
        db.commit()

        engine_codes = set(db.scalars(select(GenerativeEngine.code)).all())
        expected = {s.code for s in GENERATIVE_ENGINE_SEEDS}
        assert expected <= engine_codes

        providers = {p.code: p for p in db.scalars(select(AiProvider)).all()}
        for spec in GENERATIVE_ENGINE_SEEDS:
            row = db.scalar(select(GenerativeEngine).where(GenerativeEngine.code == spec.code))
            assert row is not None
            assert row.name == spec.name
            if spec.provider_code:
                assert row.llm_provider_id == providers[spec.provider_code].id

        before = db.scalar(select(func.count()).select_from(GenerativeEngine))
        seed_dev.seed_generative_engines(db)
        db.commit()
        after = db.scalar(select(func.count()).select_from(GenerativeEngine))
        assert after == before
    finally:
        db.close()
