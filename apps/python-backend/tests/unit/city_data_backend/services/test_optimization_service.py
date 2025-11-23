from __future__ import annotations

import json
import os
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Mapping

from city_data_backend.database import configure_engine, get_session
from city_data_backend.services.datasets import init_database
from city_data_backend.services.optimization import OptimizationService, TrainsetExample


class DummyGenerator:
    """Return a fixed query_spec per question for deterministic scoring."""

    def __init__(self, mapping: dict[str, dict[str, object]]) -> None:
        """Store question -> query_spec mapping."""
        self.mapping = mapping

    def generate(self, question: str, _meta: Mapping[str, object]) -> dict[str, object]:
        """Return the pre-defined query_spec for the question."""
        return self.mapping[question]


def _prepare_trainset(tmp_path: Path) -> Path:
    trainset: list[TrainsetExample] = [
        {
            "question": "人口を集計したい",
            "dataset_meta": {"id": 1},
            "query_spec": {"filters": [], "group_by": ["ward"], "metrics": []},
        },
        {
            "question": "件数だけ知りたい",
            "dataset_meta": {"id": 1},
            "query_spec": {"filters": [], "group_by": [], "metrics": []},
        },
    ]
    path = tmp_path / "trainset.json"
    path.write_text(json.dumps(trainset, ensure_ascii=False))
    return path


def _setup_database() -> None:
    os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:?cache=shared"
    configure_engine(os.environ["DATABASE_URL"])
    session = get_session()
    init_database(session)


def test_compile_interactive_persists_artifact(tmp_path: Path) -> None:
    """Compilation writes artifact metadata and metrics to disk and DB."""
    _setup_database()
    trainset_path = _prepare_trainset(tmp_path)
    mapping: dict[str, dict[str, object]] = {
        "人口を集計したい": {"group_by": ["ward"], "metrics": []},
        "件数だけ知りたい": {"group_by": [], "metrics": []},
    }
    service = OptimizationService(
        session=get_session(),
        artifact_root=tmp_path,
        generator=DummyGenerator(mapping).generate,
    )

    result = service.compile_interactive(trainset_path, version="v-test")

    assert result.version == "v-test"
    assert result.baseline_score == 1.0
    assert result.compiled_score == 1.0
    artifact_path = Path(result.artifact.path)
    assert artifact_path.exists()
    assert artifact_path.parent == tmp_path


def test_load_trainset_rejects_invalid_payload(tmp_path: Path) -> None:
    """Non-list trainsets raise a clear validation error."""
    _setup_database()
    invalid = tmp_path / "trainset.json"
    invalid.write_text(json.dumps({"question": "oops"}))
    service = OptimizationService(session=get_session(), artifact_root=tmp_path)

    with pytest.raises(TypeError, match="Trainset JSON"):
        service.load_trainset(invalid)
