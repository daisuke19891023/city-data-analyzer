# ruff: noqa: N818

from collections.abc import Callable
from typing import Any, TypeVar

__all__ = [
    "Depends",
    "FastAPI",
    "HTTPException",
    "status",
]

_F = TypeVar("_F", bound=Callable[..., Any])

class HTTPException(Exception):
    status_code: int
    detail: Any
    headers: dict[str, str] | None

    def __init__(
        self,
        status_code: int,
        detail: Any = ...,
        headers: dict[str, str] | None = None,
    ) -> None: ...

class _Depends:
    dependency: Callable[..., Any] | None
    use_cache: bool

    def __init__(
        self,
        dependency: Callable[..., Any] | None = None,
        *,
        use_cache: bool = True,
    ) -> None: ...

def Depends(
    dependency: Callable[..., Any] | None = None,
    *,
    use_cache: bool = True,
) -> _Depends: ...

class _Status:
    HTTP_200_OK: int
    HTTP_201_CREATED: int
    HTTP_404_NOT_FOUND: int

status: _Status

class FastAPI:
    title: str
    version: str

    def __init__(
        self,
        *,
        title: str = "FastAPI",
        description: str = "",
        version: str = "0.1.0",
        **kwargs: Any,
    ) -> None: ...
    def get(
        self,
        path: str,
        *,
        response_model: Any = None,
        response_class: Any = None,
        status_code: int = 200,
        tags: list[str] | None = None,
        dependencies: list[Any] | None = None,
        summary: str | None = None,
        description: str | None = None,
        response_description: str = "Successful Response",
        responses: dict[int | str, dict[str, Any]] | None = None,
        deprecated: bool | None = None,
        operation_id: str | None = None,
        response_model_include: Any = None,
        response_model_exclude: Any = None,
        response_model_by_alias: bool = True,
        response_model_exclude_unset: bool = False,
        response_model_exclude_defaults: bool = False,
        response_model_exclude_none: bool = False,
        include_in_schema: bool = True,
        name: str | None = None,
        callbacks: list[Any] | None = None,
        openapi_extra: dict[str, Any] | None = None,
        generate_unique_id_function: Callable[..., str] | None = None,
    ) -> Callable[[_F], _F]: ...
    def post(
        self,
        path: str,
        *,
        response_model: Any = None,
        response_class: Any = None,
        status_code: int = 200,
        tags: list[str] | None = None,
        dependencies: list[Any] | None = None,
        summary: str | None = None,
        description: str | None = None,
        response_description: str = "Successful Response",
        responses: dict[int | str, dict[str, Any]] | None = None,
        deprecated: bool | None = None,
        operation_id: str | None = None,
        response_model_include: Any = None,
        response_model_exclude: Any = None,
        response_model_by_alias: bool = True,
        response_model_exclude_unset: bool = False,
        response_model_exclude_defaults: bool = False,
        response_model_exclude_none: bool = False,
        include_in_schema: bool = True,
        name: str | None = None,
        callbacks: list[Any] | None = None,
        openapi_extra: dict[str, Any] | None = None,
        generate_unique_id_function: Callable[..., str] | None = None,
    ) -> Callable[[_F], _F]: ...
    def on_event(self, event_type: str) -> Callable[[_F], _F]: ...

    routes: list[Any]
