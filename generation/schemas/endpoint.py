"""Endpoint registry for tying save operations to OpenAPI spec generation.

This module provides a declarative way to define API endpoints that automatically
generates OpenAPI specifications from the same definitions used for file writes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel


@dataclass
class EndpointParam:
    """Path parameter definition."""

    name: str
    description: str
    example: str | None = None


@dataclass
class Endpoint:
    """Definition of an API endpoint that maps to a file write operation."""

    path: str
    summary: str
    tags: list[str]
    description: str | None = None
    # Schema can be a Pydantic model class, a dict (inline schema), or None
    response_model: type[BaseModel] | None = None
    response_schema: dict[str, Any] | None = None
    is_array: bool = False
    params: list[EndpointParam] = field(default_factory=list)
    operation_id: str | None = None

    def get_operation_id(self) -> str:
        """Generate operation ID from path if not specified."""
        if self.operation_id:
            return self.operation_id
        # Convert /course/{courseId} -> getCourse
        parts = self.path.strip("/").split("/")
        name = "".join(p.title().replace("{", "").replace("}", "") for p in parts)
        return f"get{name}"

    def get_response_schema(self, use_refs: bool = True) -> dict[str, Any]:
        """Get the response schema definition."""
        if self.response_schema:
            return self.response_schema

        if self.response_model:
            if use_refs:
                ref = {"$ref": f"#/components/schemas/{self.response_model.__name__}"}
            else:
                ref = self.response_model.model_json_schema()

            if self.is_array:
                return {"type": "array", "items": ref}
            return ref

        return {"type": "object"}

    def to_openapi_path(self) -> dict[str, Any]:
        """Convert to OpenAPI path definition."""
        operation: dict[str, Any] = {
            "summary": self.summary,
            "operationId": self.get_operation_id(),
            "tags": self.tags,
            "responses": {
                "200": {
                    "description": self.description or self.summary,
                    "content": {
                        "application/json": {"schema": self.get_response_schema()}
                    },
                }
            },
        }

        if self.params:
            operation["parameters"] = [
                {
                    "name": p.name,
                    "in": "path",
                    "required": True,
                    "description": p.description,
                    "schema": {"type": "string"},
                    **({"example": p.example} if p.example else {}),
                }
                for p in self.params
            ]

        # Add 404 for parameterized paths
        if "{" in self.path:
            operation["responses"]["404"] = {"description": "Not found"}

        return {"get": operation}


class EndpointRegistry:
    """Registry for collecting endpoint definitions."""

    _instance: EndpointRegistry | None = None
    _endpoints: list[Endpoint]
    _models: set[type[BaseModel]]

    def __new__(cls) -> EndpointRegistry:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._endpoints = []
            cls._instance._models = set()
        return cls._instance

    def register(self, endpoint: Endpoint) -> Endpoint:
        """Register an endpoint definition."""
        self._endpoints.append(endpoint)
        if endpoint.response_model:
            self._models.add(endpoint.response_model)
        return endpoint

    def get_endpoints(self) -> list[Endpoint]:
        """Get all registered endpoints."""
        return self._endpoints.copy()

    def get_models(self) -> set[type[BaseModel]]:
        """Get all Pydantic models used in endpoints."""
        return self._models.copy()

    def clear(self) -> None:
        """Clear all registered endpoints (useful for testing)."""
        self._endpoints.clear()
        self._models.clear()

    @classmethod
    def reset(cls) -> None:
        """Reset the singleton instance."""
        cls._instance = None


# Global registry instance
registry = EndpointRegistry()


def endpoint(
    path: str,
    summary: str,
    tags: list[str],
    description: str | None = None,
    response_model: type[BaseModel] | None = None,
    response_schema: dict[str, Any] | None = None,
    is_array: bool = False,
    params: list[EndpointParam] | None = None,
    operation_id: str | None = None,
) -> Endpoint:
    """Create and register an endpoint definition.

    This is the primary way to define endpoints. Each endpoint maps to a
    file that will be written by save.py.

    Example:
        # Define a simple endpoint
        SUBJECTS = endpoint(
            path="/subjects",
            summary="Get all subject codes and names",
            tags=["Metadata"],
            response_schema={"type": "object", "additionalProperties": {"type": "string"}},
        )

        # Define an endpoint with a Pydantic model
        COURSE = endpoint(
            path="/course/{courseId}",
            summary="Get course by ID",
            tags=["Courses"],
            response_model=Course,
            params=[EndpointParam("courseId", "Course identifier", "COMPSCI_200")],
        )
    """
    ep = Endpoint(
        path=path,
        summary=summary,
        tags=tags,
        description=description,
        response_model=response_model,
        response_schema=response_schema,
        is_array=is_array,
        params=params or [],
        operation_id=operation_id,
    )
    registry.register(ep)
    return ep
