"""API endpoint definitions.

This is the single source of truth for all API endpoints. These definitions are used by:
1. save.py - to know what files to write and their structure
2. openapi.py - to generate the OpenAPI specification

When adding a new endpoint:
1. Add the endpoint definition here
2. Add the corresponding write_file() call in save.py
3. The OpenAPI spec will automatically include the new endpoint
"""

from schemas.course import Course
from schemas.enrollment import Meeting
from schemas.instructor import FullInstructor
from schemas.endpoint import endpoint, EndpointParam

# =============================================================================
# Metadata Endpoints
# =============================================================================

SUBJECTS = endpoint(
    path="/subjects",
    summary="Get all subject codes and names",
    tags=["Metadata"],
    response_schema={"type": "object", "additionalProperties": {"type": "string"}},
)

TERMS = endpoint(
    path="/terms",
    summary="Get all term codes and names",
    tags=["Metadata"],
    response_schema={"type": "object", "additionalProperties": {"type": "string"}},
)

UPDATE = endpoint(
    path="/update",
    summary="Get last update timestamp",
    tags=["Metadata"],
    response_schema={
        "type": "object",
        "properties": {"updated_on": {"type": "string", "format": "date-time"}},
    },
)

MANIFEST = endpoint(
    path="/manifest",
    summary="Get API manifest",
    description="Lists all available resources for discovery",
    tags=["Metadata"],
    response_schema={
        "type": "object",
        "properties": {
            "subjects": {"type": "array", "items": {"type": "string"}},
            "courses": {"type": "array", "items": {"type": "string"}},
            "instructors": {"type": "array", "items": {"type": "string"}},
            "updated_on": {"type": "string", "format": "date-time"},
        },
    },
)

# =============================================================================
# Course Endpoints
# =============================================================================

COURSE = endpoint(
    path="/course/{courseId}",
    summary="Get course by ID",
    tags=["Courses"],
    response_model=Course,
    params=[
        EndpointParam(
            name="courseId",
            description="Course identifier (e.g., COMPSCI_200)",
            example="COMPSCI_200",
        )
    ],
)

COURSE_MEETINGS = endpoint(
    path="/course/{courseId}/meetings",
    summary="Get course meetings",
    tags=["Courses", "Meetings"],
    response_model=Meeting,
    is_array=True,
    params=[EndpointParam(name="courseId", description="Course identifier")],
)

# =============================================================================
# Instructor Endpoints
# =============================================================================

INSTRUCTOR = endpoint(
    path="/instructors/{instructorId}",
    summary="Get instructor by ID",
    tags=["Instructors"],
    response_model=FullInstructor,
    params=[
        EndpointParam(
            name="instructorId",
            description="Instructor identifier (sanitized name)",
            example="JOHN_DOE",
        )
    ],
)

INSTRUCTOR_MEETINGS = endpoint(
    path="/instructors/{instructorId}/meetings",
    summary="Get instructor meetings",
    tags=["Instructors", "Meetings"],
    response_model=Meeting,
    is_array=True,
    params=[EndpointParam(name="instructorId", description="Instructor identifier")],
)

# =============================================================================
# Graph Endpoints
# =============================================================================

GLOBAL_GRAPH = endpoint(
    path="/global_graph",
    summary="Get global prerequisite graph",
    tags=["Graphs"],
    response_schema={"type": "array", "items": {"type": "object"}},
)

SUBJECT_GRAPH = endpoint(
    path="/graphs/{subject}",
    summary="Get subject prerequisite graph",
    tags=["Graphs"],
    response_schema={
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
                    },
                }
            },
        },
    },
    params=[
        EndpointParam(name="subject", description="Subject code", example="COMPSCI")
    ],
)

COURSE_GRAPH = endpoint(
    path="/graphs/course/{courseId}",
    summary="Get course prerequisite graph",
    tags=["Graphs"],
    response_schema={"type": "array", "items": {"type": "object"}},
    params=[EndpointParam(name="courseId", description="Course identifier")],
)

GLOBAL_STYLE = endpoint(
    path="/global_style",
    summary="Get global graph style",
    tags=["Graphs"],
    response_schema={"type": "array", "items": {"type": "object"}},
)

SUBJECT_STYLE = endpoint(
    path="/styles/{subject}",
    summary="Get subject graph style",
    tags=["Graphs"],
    response_schema={"type": "array", "items": {"type": "object"}},
    params=[EndpointParam(name="subject", description="Subject code")],
)

# =============================================================================
# Statistics Endpoints
# =============================================================================

QUICK_STATISTICS = endpoint(
    path="/quick_statistics",
    summary="Get quick statistics",
    tags=["Statistics"],
    response_schema={
        "type": "object",
        "properties": {
            "total_courses": {"type": "integer"},
            "total_instructors": {"type": "integer"},
            "total_ratings": {"type": "integer"},
            "total_detected_requisites": {"type": "integer"},
            "total_grades_given": {"$ref": "#/components/schemas/GradeData"},
        },
    },
)

SUBJECT_STATS = endpoint(
    path="/stats/{subject}",
    summary="Get subject statistics",
    tags=["Statistics"],
    response_schema={
        "type": "object",
        "properties": {
            "total_courses": {"type": "integer"},
            "total_detected_requisites": {"type": "integer"},
            "total_grades_given": {"$ref": "#/components/schemas/GradeData"},
        },
    },
    params=[EndpointParam(name="subject", description="Subject code")],
)

# =============================================================================
# Meeting Endpoints
# =============================================================================

BUILDING_MEETINGS = endpoint(
    path="/buildings/{buildingName}/meetings",
    summary="Get meetings by building",
    tags=["Meetings", "Buildings"],
    response_model=Meeting,
    is_array=True,
    params=[EndpointParam(name="buildingName", description="Building name")],
)

DATE_MEETINGS = endpoint(
    path="/meetings/{date}",
    summary="Get meetings by date",
    tags=["Meetings"],
    response_model=Meeting,
    is_array=True,
    params=[
        EndpointParam(
            name="date",
            description="Date in MM-DD-YY format",
            example="01-15-25",
        )
    ],
)

MEETINGS_INDEX = endpoint(
    path="/meetings/index",
    summary="Get meetings index with date statistics",
    tags=["Meetings"],
    response_schema={
        "type": "object",
        "additionalProperties": {
            "type": "object",
            "properties": {
                "total_buildings": {"type": "integer"},
                "total_meetings": {"type": "integer"},
                "total_instructors": {"type": "integer"},
                "total_students": {"type": "integer"},
            },
        },
    },
)

SUBJECT_MEETINGS = endpoint(
    path="/subjects/{subject}/meetings",
    summary="Get meetings by subject",
    tags=["Meetings"],
    response_model=Meeting,
    is_array=True,
    params=[EndpointParam(name="subject", description="Subject code")],
)

BUILDING_DATE_MEETINGS = endpoint(
    path="/buildings/{buildingName}/{date}",
    summary="Get building meetings for a specific date",
    tags=["Meetings", "Buildings"],
    response_model=Meeting,
    is_array=True,
    params=[
        EndpointParam(name="buildingName", description="Building name"),
        EndpointParam(name="date", description="Date in MM-DD-YY format"),
    ],
)
