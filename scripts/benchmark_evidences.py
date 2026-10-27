import time
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.models.database import Base, DocumentModel, ProcessingRunModel, EvidenceModel

def run_merge_loop(db, run_id, doc_id, evidences_data):
    id_map = {}
    for idx, ev_data in enumerate(evidences_data, 1):
        raw_id = ev_data.get("id") or f"ev-{run_id[:8]}-{idx}"
        scoped_id = f"{raw_id}-{run_id[:8]}" if not raw_id.endswith(run_id[:8]) else raw_id
        id_map[raw_id] = scoped_id
        ev = EvidenceModel(
            id=scoped_id,
            document_id=doc_id,
            run_id=run_id,
            page=ev_data.get("page", 1),
            bbox=ev_data.get("bbox"),
            coordinate_system=ev_data.get("coordinate_system", "NORMALIZED_0_1"),
            localization_status=ev_data.get("localization_status", "UNLOCALIZED"),
            source=ev_data.get("source", "VLM_OUTPUT"),
            excerpt=ev_data.get("excerpt"),
        )
        db.merge(ev)
    db.flush()
    return id_map

def run_add_all(db, run_id, doc_id, evidences_data):
    id_map = {}
    ev_models = []
    for idx, ev_data in enumerate(evidences_data, 1):
        raw_id = ev_data.get("id") or f"ev-{run_id[:8]}-{idx}"
        scoped_id = f"{raw_id}-{run_id[:8]}" if not raw_id.endswith(run_id[:8]) else raw_id
        id_map[raw_id] = scoped_id
        ev = EvidenceModel(
            id=scoped_id,
            document_id=doc_id,
            run_id=run_id,
            page=ev_data.get("page", 1),
            bbox=ev_data.get("bbox"),
            coordinate_system=ev_data.get("coordinate_system", "NORMALIZED_0_1"),
            localization_status=ev_data.get("localization_status", "UNLOCALIZED"),
            source=ev_data.get("source", "VLM_OUTPUT"),
            excerpt=ev_data.get("excerpt"),
        )
        ev_models.append(ev)
    db.add_all(ev_models)
    db.flush()
    return id_map

def benchmark():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)

    batch_sizes = [100, 500, 2000]

    for count in batch_sizes:
        print(f"\n--- Batch Size: {count} ---")
        evidences_data = [
            {
                "id": f"ev-test-{i}",
                "page": 1,
                "bbox": {"x_min": 0.1, "y_min": 0.2, "x_max": 0.3, "y_max": 0.4},
                "coordinate_system": "NORMALIZED_0_1",
                "localization_status": "VALIDATED",
                "source": "VLM_OUTPUT",
                "excerpt": f"Excerpt sample content {i}"
            }
            for i in range(count)
        ]

        # Benchmark db.merge loop
        db = Session()
        doc = DocumentModel(id=f"doc-m-{count}", filename_original="a.jpg", storage_key=f"sk-m-{count}", content_hash=f"hash-m-{count}", media_type="image/jpeg", width=100, height=100)
        run = ProcessingRunModel(id=f"m-{count}-run", document_id=doc.id, mode="DEMO", provider="Demo", model_id="m1")
        db.add(doc)
        db.add(run)
        db.commit()

        t0 = time.perf_counter()
        run_merge_loop(db, run.id, doc.id, evidences_data)
        db.commit()
        t1 = time.perf_counter()
        merge_time = (t1 - t0) * 1000
        print(f"db.merge loop time: {merge_time:.2f} ms")
        db.close()

        # Benchmark db.add_all
        db = Session()
        doc = DocumentModel(id=f"doc-a-{count}", filename_original="a.jpg", storage_key=f"sk-a-{count}", content_hash=f"hash-a-{count}", media_type="image/jpeg", width=100, height=100)
        run = ProcessingRunModel(id=f"a-{count}-run", document_id=doc.id, mode="DEMO", provider="Demo", model_id="m1")
        db.add(doc)
        db.add(run)
        db.commit()

        t0 = time.perf_counter()
        run_add_all(db, run.id, doc.id, evidences_data)
        db.commit()
        t1 = time.perf_counter()
        add_all_time = (t1 - t0) * 1000
        print(f"db.add_all time:    {add_all_time:.2f} ms")
        speedup = merge_time / add_all_time if add_all_time > 0 else float('inf')
        print(f"Speedup:            {speedup:.2f}x")
        db.close()

if __name__ == "__main__":
    benchmark()
