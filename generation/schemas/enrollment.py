"""Enrollment-related Pydantic models."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, field_serializer

from schemas.grades import GradeData


class School(BaseModel):
    """School/college information."""

    name: str
    abbreviation: str
    url: str | None

    @classmethod
    def from_enrollment(cls, data: dict) -> School:
        """Create School from enrollment API response."""
        return cls(
            name=data["shortDescription"],
            abbreviation=data["academicOrgCode"],
            url=data["schoolCollegeURI"],
        )


class MeetingLocation(BaseModel):
    """Physical location for a class meeting."""

    model_config = ConfigDict(frozen=True)

    building: str | None
    room: str | None
    coordinates: tuple[float, float] | None = None
    capacity: int | None = None

    def __hash__(self) -> int:
        return hash((self.building, self.room, self.coordinates))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, MeetingLocation):
            return False
        return (
            self.building == other.building
            and self.room == other.room
            and self.coordinates == other.coordinates
        )


class Meeting(BaseModel):
    """A class meeting/section."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str
    type: str
    start_time: int | None
    end_time: int | None
    location: MeetingLocation | None = None
    current_enrollment: int | None = None
    instructors: list[str] = []
    course_reference: Any | None = None  # CourseReference

    @field_serializer("course_reference")
    def serialize_course_ref(self, ref: Any) -> dict | None:
        """Serialize course reference if present."""
        if ref is None:
            return None
        if hasattr(ref, "model_dump"):
            return ref.model_dump()
        return None

    def __hash__(self) -> int:
        section = self.name.split("#")[0].strip() if self.name else ""
        return hash(
            (
                section,
                self.type,
                self.start_time,
                self.end_time,
                tuple(sorted(self.instructors)),
            )
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Meeting):
            return False

        self_section = self.name.split("#")[0].strip() if self.name else ""
        other_section = other.name.split("#")[0].strip() if other.name else ""

        return (
            self_section == other_section
            and self.type == other.type
            and self.start_time == other.start_time
            and self.end_time == other.end_time
            and sorted(self.instructors) == sorted(other.instructors)
        )


class EnrollmentData(BaseModel):
    """Enrollment information for a course in a specific term."""

    school: School | None = None
    last_taught_term: str | None = None
    typically_offered: str | None = None
    credit_count: tuple[int, int] = (0, 0)
    general_education: bool = False
    ethnics_studies: bool = False
    instructors: dict[str, str | None] = {}

    @field_serializer("credit_count")
    def serialize_credit_count(self, credit_count: tuple[int, int]) -> list[int]:
        """Serialize credit count tuple as list."""
        return [credit_count[0], credit_count[1]]

    @classmethod
    def from_enrollment(cls, data: dict, terms: dict[int, str]) -> EnrollmentData:
        """Create EnrollmentData from enrollment API response."""
        from safe_parse import safe_int

        last_taught_term_code = safe_int(data.get("lastTaught"))
        last_taught_term = None
        if last_taught_term_code and last_taught_term_code in terms:
            last_taught_term = terms[last_taught_term_code]

        return cls(
            school=School.from_enrollment(data["subject"]["schoolCollege"]),
            last_taught_term=last_taught_term,
            typically_offered=data.get("typicallyOffered"),
            credit_count=(data["minimumCredits"], data["maximumCredits"]),
            general_education=data.get("generalEd") is not None,
            ethnics_studies=data.get("ethnicStudies") is not None,
            instructors={},
        )


class TermData(BaseModel):
    """Data for a specific term including enrollment and grade information."""

    enrollment_data: EnrollmentData | None = None
    grade_data: GradeData | None = None
