"""FastAPI application instance for running the REST API."""

from city_data_backend.interfaces.restapi import RestAPIInterface

# Instantiate once so `uvicorn city_data_backend.api:app` works out of the box
_interface = RestAPIInterface()
app = _interface.app

__all__ = ["app"]
