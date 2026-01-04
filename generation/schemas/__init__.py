"""Pydantic schemas for UW Course Map data generation."""

from schemas.grades import GradeData
from schemas.course import (
    CourseReference,
    CoursePrerequisites,
    Course,
)
from schemas.enrollment import (
    School,
    MeetingLocation,
    Meeting,
    EnrollmentData,
    TermData,
)
from schemas.instructor import (
    MandatoryAttendance,
    RatingsDistribution,
    Rating,
    RMPData,
    FullInstructor,
)
from schemas.requirement_ast import (
    Leaf,
    Node,
    RequirementAbstractSyntaxTree,
)

__all__ = [
    # Grades
    "GradeData",
    # Course
    "CourseReference",
    "CoursePrerequisites",
    "TermData",
    "Course",
    # Enrollment
    "School",
    "MeetingLocation",
    "Meeting",
    "EnrollmentData",
    # Instructor
    "MandatoryAttendance",
    "RatingsDistribution",
    "Rating",
    "RMPData",
    "FullInstructor",
    # Requirement AST
    "Leaf",
    "Node",
    "RequirementAbstractSyntaxTree",
]
