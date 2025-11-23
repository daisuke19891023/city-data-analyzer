"""Type definitions for the City Data Backend."""

from enum import Enum


class InterfaceType(str, Enum):
    """Available interface types."""

    CLI = "cli"
    RESTAPI = "restapi"
    MCP = "mcp"
