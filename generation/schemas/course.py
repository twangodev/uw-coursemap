"""Course-related Pydantic models."""

from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, ConfigDict, field_serializer, field_validator

from schemas.grades import GradeData
from schemas.enrollment import TermData


def remove_extra_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def cleanup_course_reference_str(course_code: str) -> str | None:
    """Remove special HTML characters and clean up the course code."""
    if not course_code:
        return None
    course_code = remove_extra_spaces(course_code)
    return course_code.replace("\u200b", " ").replace("\u00a0", " ").strip()


class CourseReference(BaseModel):
    """Reference to a course by subject codes and number."""

    model_config = ConfigDict(frozen=True)

    subjects: frozenset[str]
    course_number: int

    @field_validator("subjects", mode="before")
    @classmethod
    def convert_subjects(cls, v: Any) -> frozenset[str]:
        """Convert list/set to frozenset for hashability."""
        if isinstance(v, (list, set)):
            return frozenset(v)
        return v

    @field_serializer("subjects")
    def serialize_subjects(self, subjects: frozenset[str]) -> list[str]:
        """Serialize frozenset as sorted list for consistent JSON output."""
        return sorted(subjects)

    @classmethod
    def from_string(cls, course_reference_str: str) -> CourseReference:
        """Parse a course reference from a string like 'CS/ECE 252'."""
        course_reference_str = cleanup_course_reference_str(course_reference_str)
        if not course_reference_str:
            raise ValueError("Empty course reference string")

        match = re.match(r"(\D+)(\d+)", course_reference_str)
        if not match:
            raise ValueError(f"Invalid course reference format: {course_reference_str}")

        course_subject_str = match.group(1).replace(" ", "").strip()
        raw_course_subjects = course_subject_str.split("/")
        course_subjects = frozenset(
            subject.replace(" ", "") for subject in raw_course_subjects
        )
        course_number = int(match.group(2).strip())

        return cls(subjects=course_subjects, course_number=course_number)

    def get_identifier(self) -> str:
        """Get a string identifier for this course reference."""
        subjects = "/".join(sorted(self.subjects))
        return f"{subjects} {self.course_number}"

    def __hash__(self) -> int:
        return hash((self.subjects, self.course_number))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, CourseReference):
            return False
        return (
            self.subjects == other.subjects
            and self.course_number == other.course_number
        )

    def __str__(self) -> str:
        return self.get_identifier()

    def __repr__(self) -> str:
        return f"CourseReference(subjects={set(self.subjects)}, course_number={self.course_number})"


class CoursePrerequisites(BaseModel):
    """Prerequisites information for a course."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    prerequisites_text: str
    linked_requisite_text: list[str | CourseReference]
    course_references: list[CourseReference]
    abstract_syntax_tree: Any | None = None  # RequirementAbstractSyntaxTree

    @field_serializer("linked_requisite_text")
    def serialize_linked_text(
        self, linked_text: list[str | CourseReference]
    ) -> list[str | dict]:
        """Serialize linked requisite text, converting CourseReferences to dicts."""
        result = []
        for item in linked_text:
            if isinstance(item, CourseReference):
                result.append(item.model_dump())
            else:
                result.append(str(item))
        return result

    @field_serializer("course_references")
    def serialize_course_refs(self, refs: list[CourseReference]) -> list[dict]:
        """Serialize course references to dicts."""
        return [ref.model_dump() for ref in refs]

    @field_serializer("abstract_syntax_tree")
    def serialize_ast(self, ast: Any) -> dict | str | None:
        """Serialize the AST if present."""
        if ast is None:
            return None
        if hasattr(ast, "model_dump"):
            return ast.model_dump()
        if hasattr(ast, "to_dict"):
            return ast.to_dict()
        return None


class Course(BaseModel):
    """Complete course information."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    course_reference: CourseReference
    course_title: str
    description: str
    prerequisites: CoursePrerequisites
    optimized_prerequisites: list[CourseReference] | None = None
    cumulative_grade_data: GradeData | None = None
    term_data: dict[str, TermData]
    similar_courses: list[CourseReference] = []
    keywords: list[str] = []
    satisfies: list[CourseReference] = []
    has_meetings: bool = False

    def get_identifier(self) -> str:
        """Get the course identifier string."""
        return self.course_reference.get_identifier()

    def determine_parent(self) -> str | None:
        """Determine the parent category for graph visualization."""
        subjects = self.course_reference.subjects
        if len(subjects) > 1:
            return "CROSSLISTED"
        elif len(subjects) == 1:
            return next(iter(subjects))
        return None

    def get_short_summary(self) -> str:
        """Get a short summary of the course."""
        return f"""Course Title: {self.course_reference.get_identifier()} - {self.course_title}
        Course Description: {self.description}
        """

    def get_full_summary(self) -> str:
        """Get a full summary including prerequisites."""
        req = self.prerequisites.prerequisites_text
        return f"""{self.get_short_summary()}
        Prerequisites: {req}
        """

    def get_latest_term_data(self) -> TermData | None:
        """Get the latest term data for the course."""
        if not self.term_data:
            return None
        latest_term = max(self.term_data.keys(), key=lambda x: int(x))
        return self.term_data[latest_term]

    def __hash__(self) -> int:
        return hash(self.get_identifier())

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Course):
            return False
        return (
            self.get_identifier() == other.get_identifier()
            and self.course_title == other.course_title
            and self.description == other.description
        )

    def __repr__(self) -> str:
        return self.get_identifier()


# Rebuild model for forward references
Course.model_rebuild()
