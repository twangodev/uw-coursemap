"""OpenAPI schema generator for UW Course Map API.

Generates OpenAPI spec from endpoint definitions in endpoints.py.
"""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel

# Import endpoints to trigger registration
import schemas.endpoints  # noqa: F401
from schemas.endpoint import registry
from schemas.course import CourseReference, CoursePrerequisites
from schemas.enrollment import (
    School,
    MeetingLocation,
    EnrollmentData,
    TermData,
)
from schemas.grades import GradeData
from schemas.instructor import RMPData
from schemas.requirement_ast import RequirementAbstractSyntaxTree, Leaf, Node

DEFAULT_BASE_URL = "https://api.uwcourses.com"

# Additional Pydantic models to include in OpenAPI components
# (models not directly referenced by endpoints but used in nested schemas)
ADDITIONAL_MODELS: list[type[BaseModel]] = [
    GradeData,
    CourseReference,
    CoursePrerequisites,
    School,
    MeetingLocation,
    EnrollmentData,
    TermData,
    RMPData,
    RequirementAbstractSyntaxTree,
    Leaf,
    Node,
]


def get_component_schemas() -> dict[str, Any]:
    """Generate component schemas from Pydantic models."""
    component_schemas: dict[str, Any] = {}

    # Collect all models: from registry + additional models
    all_models = registry.get_models() | set(ADDITIONAL_MODELS)

    for model in all_models:
        schema = model.model_json_schema(ref_template="#/components/schemas/{model}")
        # Extract $defs if present
        if "$defs" in schema:
            for def_name, def_schema in schema["$defs"].items():
                if def_name not in component_schemas:
                    component_schemas[def_name] = def_schema
            del schema["$defs"]
        # Skip self-referencing schemas (recursive types)
        if schema.get("$ref") == f"#/components/schemas/{model.__name__}":
            continue
        component_schemas[model.__name__] = schema

    return component_schemas


def generate_openapi_spec(
    title: str = "UW Course Map API",
    version: str = "1.0.0",
    description: str = "Static JSON API for UW-Madison course data",
    base_url: str = DEFAULT_BASE_URL,
) -> dict[str, Any]:
    """Generate a complete OpenAPI 3.1.0 specification."""
    endpoints = registry.get_endpoints()
    paths = {ep.path: ep.to_openapi_path() for ep in endpoints}

    return {
        "openapi": "3.1.0",
        "info": {
            "title": title,
            "version": version,
            "description": description,
            "contact": {"name": "UW Course Map"},
        },
        "servers": [{"url": base_url, "description": "Production API"}],
        "tags": [
            {"name": "Metadata", "description": "API metadata and configuration"},
            {"name": "Courses", "description": "Course information"},
            {"name": "Instructors", "description": "Instructor information"},
            {"name": "Meetings", "description": "Class meetings and schedules"},
            {"name": "Graphs", "description": "Prerequisite graphs"},
            {"name": "Statistics", "description": "Aggregate statistics"},
            {"name": "Buildings", "description": "Campus building data"},
        ],
        "paths": paths,
        "components": {"schemas": get_component_schemas()},
    }


def export_openapi_spec(output_path: str = "openapi.json", **kwargs) -> None:
    """Export the OpenAPI spec to a JSON file."""
    spec = generate_openapi_spec(**kwargs)
    with open(output_path, "w") as f:
        json.dump(spec, f, indent=2)
    print(f"OpenAPI spec exported to {output_path}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate OpenAPI spec")
    parser.add_argument(
        "--output", "-o", default="openapi.json", help="Output file path"
    )
    parser.add_argument(
        "--base-url", default=DEFAULT_BASE_URL, help="Base URL for the API"
    )
    args = parser.parse_args()
    export_openapi_spec(args.output, base_url=args.base_url)
