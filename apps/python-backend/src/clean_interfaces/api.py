"""FastAPI application instance for running the REST API."""

from clean_interfaces.interfaces.restapi import RestAPIInterface

# Instantiate once so `uvicorn clean_interfaces.api:app` works out of the box
_interface = RestAPIInterface()
app = _interface.app

__all__ = ["app"]
