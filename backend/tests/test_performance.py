import os
import sys
import time
from datetime import datetime, timedelta, timezone
from PIL import Image

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.api.app import app, get_db, list_documents
from backend.models.database import (
    Base,
    DocumentModel,
    FindingModel,
    ProcessingRunModel,
    ReviewDecisionModel,
    generate_uuid,
)

# Benchmark database configuration
bench_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
BenchSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=bench_engine)
Base.metadata.create_all(bind=bench_engine)

def override_get_db():
    db = BenchSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db


def populate_benchmark_data(num_docs: int = 100):
    db = BenchSessionLocal()
    try:
        db.query(ReviewDecisionModel).delete()
        db.query(FindingModel).delete()
        db.query(ProcessingRunModel).delete()
        db.query(DocumentModel).delete()
        db.commit()

        now = datetime.now(timezone.utc)
        for i in range(num_docs):
            doc = DocumentModel(
                id=f"doc-bench-{i:04d}",
                filename_original=f"doc_{i}.jpg",
                storage_key=f"storage_key_{i}",
                content_hash=f"hash_{i:064d}",
                media_type="image/jpeg",
                width=800,
                height=600,
                synthetic=True,
                created_at=now - timedelta(minutes=num_docs - i),
            )
            db.add(doc)

            # Older run
            run_old = ProcessingRunModel(
                id=f"run-old-{i:04d}",
                document_id=doc.id,
                mode="DEMO",
                provider="DemoFixtureProvider",
                model_id="deterministic-fixture",
                status="COMPLETED",
                started_at=now - timedelta(minutes=num_docs - i, seconds=30),
            )
            db.add(run_old)

            # Latest run
            run_latest = ProcessingRunModel(
                id=f"run-latest-{i:04d}",
                document_id=doc.id,
                mode="DEMO",
                provider="DemoFixtureProvider",
                model_id="deterministic-fixture",
                status="REVIEW_REQUIRED",
                started_at=now - timedelta(minutes=num_docs - i),
            )
            db.add(run_latest)

            # Findings for latest run
            for f_idx in range(3):
                finding = FindingModel(
                    id=f"fn-{i:04d}-{f_idx}",
                    document_id=doc.id,
                    run_id=run_latest.id,
                    category="LASA_SIMILARITY",
                    severity="HIGH",
                    rule_id="MED-001",
                    title="Risk Alert",
                    explanation="Detailed explanation",
                    limitations="None",
                    requires_review=True,
                )
                db.add(finding)

            # Decisions
            dec = ReviewDecisionModel(
                id=f"dec-{i:04d}-1",
                document_id=doc.id,
                run_id=run_latest.id,
                actor_id="auditor-01",
                action="CONFIRMED_HYPOTHESIS",
                confirmed_value="Losartana 50mg",
                reason="Verified by auditor",
                created_at=now - timedelta(minutes=num_docs - i),
            )
            db.add(dec)

        db.commit()
    finally:
        db.close()


def test_list_documents_benchmark():
    num_docs = 100
    populate_benchmark_data(num_docs)

    db = BenchSessionLocal()
    query_count = 0

    def query_listener(conn, cursor, statement, parameters, context, executemany):
        nonlocal query_count
        query_count += 1

    event.listen(bench_engine, "before_cursor_execute", query_listener)

    try:
        t0 = time.perf_counter()
        results = list_documents(db=db)
        t1 = time.perf_counter()
        elapsed_ms = (t1 - t0) * 1000.0

        print(f"\n[BENCHMARK] Executed {query_count} queries for {len(results)} documents in {elapsed_ms:.2f} ms")

        assert len(results) == num_docs
        assert results[0].findings_count == 3
        assert results[0].review_status == "IN_REVIEW"
        assert results[0].last_execution_status == "REVIEW_REQUIRED"
        assert query_count <= 5, f"Expected O(1) bulk queries, got {query_count}"

    finally:
        event.remove(bench_engine, "before_cursor_execute", query_listener)
        db.close()
