"""Validate that the API entrypoint exposes all expected routes."""

from __future__ import annotations

import importlib
import sys
from typing import TYPE_CHECKING

from fastapi import FastAPI

if TYPE_CHECKING:
    import pytest


ROUTE_PATHS = {"/datasets", "/dspy/interactive", "/experiments", "/feedback"}


def test_api_entrypoint_registers_required_routes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Ensure `city_data_backend.api` exports a FastAPI app with core routes."""
    # Use in-memory database for import side effects
    monkeypatch.setenv("DATABASE_URL", "sqlite+pysqlite:///:memory:?cache=shared")

    # Reload to ensure fresh construction after env change
    sys.modules.pop("city_data_backend.api", None)
    api_module = importlib.import_module("city_data_backend.api")

    assert isinstance(api_module.app, FastAPI)
    paths = {route.path for route in api_module.app.routes}
    for path in ROUTE_PATHS:
        assert path in paths
