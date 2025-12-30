"""OpenAPI schema generator for UW Course Map API."""

from __future__ import annotations

import json
from typing import Any

from pydantic import TypeAdapter

from schemas.grades import GradeData
from schemas.course import CourseReference, CoursePrerequisites, Course
from schemas.enrollment import (
    School,
    MeetingLocation,
    Meeting,
    EnrollmentData,
    TermData,
)
from schemas.instructor import RMPData, FullInstructor
from schemas.requirement_ast import Leaf, Node, RequirementAbstractSyntaxTree


def get_all_schemas() -> dict[str, Any]:
    """Get JSON schemas for all models."""
    models = [
        GradeData,
        CourseReference,
        CoursePrerequisites,
        Course,
        School,
        MeetingLocation,
        Meeting,
        EnrollmentData,
        TermData,
        RMPData,
        FullInstructor,
    ]

    schemas = {}
    for model in models:
        schema = model.model_json_schema(ref_template="#/components/schemas/{model}")
        schemas[model.__name__] = schema

    return schemas


def generate_openapi_spec(
    title: str = "UW Course Map API",
    version: str = "1.0.0",
    description: str = "Static JSON API for UW-Madison course data",
    base_url: str = "https://api.uwcoursemap.com",
) -> dict[str, Any]:
    """Generate a complete OpenAPI 3.1.0 specification."""

    # Get component schemas
    component_schemas = {}

    # Core models with their schemas
    models = [
        GradeData,
        CourseReference,
        CoursePrerequisites,
        Course,
        School,
        MeetingLocation,
        Meeting,
        EnrollmentData,
        TermData,
        RMPData,
        FullInstructor,
    ]

    for model in models:
        schema = model.model_json_schema(ref_template="#/components/schemas/{model}")
        # Extract $defs if present and add to component schemas
        if "$defs" in schema:
            for def_name, def_schema in schema["$defs"].items():
                if def_name not in component_schemas:
                    component_schemas[def_name] = def_schema
            del schema["$defs"]
        component_schemas[model.__name__] = schema

    # Define paths
    paths = {
        "/subjects.json": {
            "get": {
                "summary": "Get all subject codes and names",
                "description": "Returns a mapping of subject codes to full subject names",
                "operationId": "getSubjects",
                "tags": ["Metadata"],
                "responses": {
                    "200": {
                        "description": "Subject code to name mapping",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "additionalProperties": {"type": "string"},
                                    "example": {
                                        "COMPSCI": "Computer Sciences",
                                        "MATH": "Mathematics",
                                    },
                                }
                            }
                        },
                    }
                },
            }
        },
        "/terms.json": {
            "get": {
                "summary": "Get all term codes and names",
                "description": "Returns a mapping of term codes to human-readable term names",
                "operationId": "getTerms",
                "tags": ["Metadata"],
                "responses": {
                    "200": {
                        "description": "Term code to name mapping",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "additionalProperties": {"type": "string"},
                                    "example": {
                                        "1252": "Fall 2024",
                                        "1254": "Spring 2025",
                                    },
                                }
                            }
                        },
                    }
                },
            }
        },
        "/update.json": {
            "get": {
                "summary": "Get last update timestamp",
                "description": "Returns when the data was last generated",
                "operationId": "getUpdateTime",
                "tags": ["Metadata"],
                "responses": {
                    "200": {
                        "description": "Update timestamp",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "updated_on": {
                                            "type": "string",
                                            "format": "date-time",
                                        }
                                    },
                                }
                            }
                        },
                    }
                },
            }
        },
        "/quick_statistics.json": {
            "get": {
                "summary": "Get quick statistics",
                "description": "Returns aggregate statistics about courses, instructors, and ratings",
                "operationId": "getQuickStatistics",
                "tags": ["Statistics"],
                "responses": {
                    "200": {
                        "description": "Quick statistics",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "total_courses": {"type": "integer"},
                                        "total_instructors": {"type": "integer"},
                                        "total_ratings": {"type": "integer"},
                                        "total_detected_requisites": {
                                            "type": "integer"
                                        },
                                        "total_grades_given": {
                                            "$ref": "#/components/schemas/GradeData"
                                        },
                                    },
                                }
                            }
                        },
                    }
                },
            }
        },
        "/course/{courseId}.json": {
            "get": {
                "summary": "Get course by ID",
                "description": "Returns detailed information about a specific course",
                "operationId": "getCourse",
                "tags": ["Courses"],
                "parameters": [
                    {
                        "name": "courseId",
                        "in": "path",
                        "required": True,
                        "description": "Course identifier (e.g., COMPSCI_200, CS_ECE_252)",
                        "schema": {"type": "string"},
                        "example": "COMPSCI_200",
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Course details",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Course"}
                            }
                        },
                    },
                    "404": {"description": "Course not found"},
                },
            }
        },
        "/course/{courseId}/meetings.json": {
            "get": {
                "summary": "Get course meetings",
                "description": "Returns all meetings/sections for a specific course",
                "operationId": "getCourseMeetings",
                "tags": ["Courses", "Meetings"],
                "parameters": [
                    {
                        "name": "courseId",
                        "in": "path",
                        "required": True,
                        "description": "Course identifier",
                        "schema": {"type": "string"},
                    }
                ],
                "responses": {
                    "200": {
                        "description": "List of meetings",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "array",
                                    "items": {"$ref": "#/components/schemas/Meeting"},
                                }
                            }
                        },
                    }
                },
            }
        },
        "/instructors/{instructorId}.json": {
            "get": {
                "summary": "Get instructor by ID",
                "description": "Returns detailed information about a specific instructor",
                "operationId": "getInstructor",
                "tags": ["Instructors"],
                "parameters": [
                    {
                        "name": "instructorId",
                        "in": "path",
                        "required": True,
                        "description": "Instructor identifier (sanitized name)",
                        "schema": {"type": "string"},
                        "example": "JOHN_DOE",
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Instructor details",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/FullInstructor"
                                }
                            }
                        },
                    },
                    "404": {"description": "Instructor not found"},
                },
            }
        },
        "/graphs/{subject}.json": {
            "get": {
                "summary": "Get subject prerequisite graph",
                "description": "Returns the prerequisite graph for a specific subject",
                "operationId": "getSubjectGraph",
                "tags": ["Graphs"],
                "parameters": [
                    {
                        "name": "subject",
                        "in": "path",
                        "required": True,
                        "description": "Subject code",
                        "schema": {"type": "string"},
                        "example": "COMPSCI",
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Cytoscape-compatible graph data",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "data": {
                                                "type": "object",
                                                "properties": {
                                                    "id": {"type": "string"},
                                                    "source": {"type": "string"},
                                                    "target": {"type": "string"},
                                                    "parent": {"type": "string"},
                                                    "title": {"type": "string"},
                                                    "description": {"type": "string"},
                                                },
                                            }
                                        },
                                    },
                                }
                            }
                        },
                    }
                },
            }
        },
        "/global_graph.json": {
            "get": {
                "summary": "Get global prerequisite graph",
                "description": "Returns the complete prerequisite graph for all courses",
                "operationId": "getGlobalGraph",
                "tags": ["Graphs"],
                "responses": {
                    "200": {
                        "description": "Cytoscape-compatible graph data",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "array",
                                    "items": {"type": "object"},
                                }
                            }
                        },
                    }
                },
            }
        },
        "/stats/{subject}.json": {
            "get": {
                "summary": "Get subject statistics",
                "description": "Returns aggregate statistics for a specific subject",
                "operationId": "getSubjectStats",
                "tags": ["Statistics"],
                "parameters": [
                    {
                        "name": "subject",
                        "in": "path",
                        "required": True,
                        "description": "Subject code",
                        "schema": {"type": "string"},
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Subject statistics",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "total_courses": {"type": "integer"},
                                        "total_detected_requisites": {
                                            "type": "integer"
                                        },
                                        "total_grades_given": {
                                            "$ref": "#/components/schemas/GradeData"
                                        },
                                    },
                                }
                            }
                        },
                    }
                },
            }
        },
        "/buildings/{buildingName}/meetings.json": {
            "get": {
                "summary": "Get meetings by building",
                "description": "Returns all meetings at a specific building",
                "operationId": "getBuildingMeetings",
                "tags": ["Meetings", "Buildings"],
                "parameters": [
                    {
                        "name": "buildingName",
                        "in": "path",
                        "required": True,
                        "description": "Building name",
                        "schema": {"type": "string"},
                    }
                ],
                "responses": {
                    "200": {
                        "description": "List of meetings",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "array",
                                    "items": {"$ref": "#/components/schemas/Meeting"},
                                }
                            }
                        },
                    }
                },
            }
        },
        "/meetings/{date}.json": {
            "get": {
                "summary": "Get meetings by date",
                "description": "Returns all meetings for a specific date",
                "operationId": "getMeetingsByDate",
                "tags": ["Meetings"],
                "parameters": [
                    {
                        "name": "date",
                        "in": "path",
                        "required": True,
                        "description": "Date in MM-DD-YY format",
                        "schema": {"type": "string"},
                        "example": "01-15-25",
                    }
                ],
                "responses": {
                    "200": {
                        "description": "List of meetings",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "array",
                                    "items": {"$ref": "#/components/schemas/Meeting"},
                                }
                            }
                        },
                    }
                },
            }
        },
    }

    # Build the OpenAPI spec
    openapi_spec = {
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
        "components": {"schemas": component_schemas},
    }

    return openapi_spec


def export_openapi_spec(
    output_path: str = "openapi.json",
    **kwargs,
) -> None:
    """Export the OpenAPI spec to a JSON file."""
    spec = generate_openapi_spec(**kwargs)
    with open(output_path, "w") as f:
        json.dump(spec, f, indent=2)
    print(f"OpenAPI spec exported to {output_path}")


def export_json_schemas(output_path: str = "schemas.json") -> None:
    """Export all JSON schemas to a file."""
    schemas = get_all_schemas()
    with open(output_path, "w") as f:
        json.dump(schemas, f, indent=2)
    print(f"JSON schemas exported to {output_path}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate OpenAPI spec")
    parser.add_argument(
        "--output",
        "-o",
        default="openapi.json",
        help="Output file path",
    )
    parser.add_argument(
        "--base-url",
        default="https://api.uwcoursemap.com",
        help="Base URL for the API",
    )
    parser.add_argument(
        "--schemas-only",
        action="store_true",
        help="Export only JSON schemas without OpenAPI wrapper",
    )

    args = parser.parse_args()

    if args.schemas_only:
        export_json_schemas(args.output)
    else:
        export_openapi_spec(args.output, base_url=args.base_url)
