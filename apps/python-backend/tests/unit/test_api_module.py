"""Ensure FastAPI app is exposed for the REST interface."""

from fastapi import FastAPI

from city_data_backend.api import app


def test_api_module_exposes_fastapi_app() -> None:
    """Importing the api module should provide a FastAPI app with health route."""
    assert isinstance(app, FastAPI)

    # A simple sanity check that a known route from RestAPIInterface is registered
    paths = {route.path for route in app.routes}
    assert "/health" in paths
