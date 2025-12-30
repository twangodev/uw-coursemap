"""Enrollment data models - now using Pydantic schemas."""

from __future__ import annotations

import asyncio
from json import JSONDecodeError
from logging import getLogger
from typing import ClassVar

from pydantic import ConfigDict

from schemas.grades import GradeData as _GradeDataBase
from schemas.enrollment import (
    School,
    MeetingLocation as _MeetingLocationBase,
    Meeting as _MeetingBase,
    EnrollmentData as _EnrollmentDataBase,
    TermData,
)
from safe_parse import safe_int

logger = getLogger(__name__)

# Re-export TermData and School directly (no modifications needed)
__all__ = [
    "School",
    "MeetingLocation",
    "Meeting",
    "EnrollmentData",
    "TermData",
    "GradeData",
    "MadgradesData",
]


class GradeData(_GradeDataBase):
    """Extended GradeData with set-based instructors for internal processing."""

    model_config = ConfigDict(
        populate_by_name=True,
        # Allow mutation for the instructors field during processing
        frozen=False,
    )

    # Override to use set internally for efficient operations
    _instructors_set: set[str] | None = None

    def __init__(self, **data):
        # Convert list to set if needed for internal processing
        instructors = data.get("instructors")
        if isinstance(instructors, list):
            self._instructors_set = set(instructors) if instructors else None
        elif isinstance(instructors, set):
            self._instructors_set = instructors
            data["instructors"] = list(instructors) if instructors else None
        super().__init__(**data)

    @property
    def instructors_as_set(self) -> set[str] | None:
        """Get instructors as a set for internal processing."""
        if self._instructors_set is not None:
            return self._instructors_set
        if self.instructors is not None:
            return set(self.instructors)
        return None

    @classmethod
    def empty(cls) -> GradeData:
        """Create an empty GradeData instance with all zeros."""
        return cls(
            total=0,
            a=0,
            ab=0,
            b=0,
            bc=0,
            c=0,
            d=0,
            f=0,
            satisfactory=0,
            unsatisfactory=0,
            credit=0,
            no_credit=0,
            passed=0,
            incomplete=0,
            no_work=0,
            not_reported=0,
            other=0,
            instructors=[],
        )

    def merge_with(self, other: GradeData | None) -> GradeData:
        """Merge this grade data with another, summing all values."""
        if not other:
            return self

        self_instructors = self.instructors_as_set
        other_instructors = (
            other.instructors_as_set
            if hasattr(other, "instructors_as_set")
            else (set(other.instructors) if other.instructors else None)
        )

        merged_instructors: list[str] | None = None
        if self_instructors is not None and other_instructors is not None:
            merged_instructors = list(self_instructors | other_instructors)
        elif self_instructors is not None:
            merged_instructors = list(self_instructors)
        elif other_instructors is not None:
            merged_instructors = list(other_instructors)

        return GradeData(
            total=self.total + other.total,
            a=self.a + other.a,
            ab=self.ab + other.ab,
            b=self.b + other.b,
            bc=self.bc + other.bc,
            c=self.c + other.c,
            d=self.d + other.d,
            f=self.f + other.f,
            satisfactory=self.satisfactory + other.satisfactory,
            unsatisfactory=self.unsatisfactory + other.unsatisfactory,
            credit=self.credit + other.credit,
            no_credit=self.no_credit + other.no_credit,
            passed=self.passed + other.passed,
            incomplete=self.incomplete + other.incomplete,
            no_work=self.no_work + other.no_work,
            not_reported=self.not_reported + other.not_reported,
            other=self.other + other.other,
            instructors=merged_instructors,
        )

    @classmethod
    def from_madgrades(cls, json_data: dict) -> GradeData:
        """Create GradeData from Madgrades API response format."""
        return cls(
            total=json_data["total"],
            a=json_data["aCount"],
            ab=json_data["abCount"],
            b=json_data["bCount"],
            bc=json_data["bcCount"],
            c=json_data["cCount"],
            d=json_data["dCount"],
            f=json_data["fCount"],
            satisfactory=json_data["sCount"],
            unsatisfactory=json_data["uCount"],
            credit=json_data["crCount"],
            no_credit=json_data["nCount"],
            passed=json_data["pCount"],
            incomplete=json_data["iCount"],
            no_work=json_data["nwCount"],
            not_reported=json_data["nrCount"],
            other=json_data["otherCount"],
            instructors=None,
        )

    @classmethod
    def from_json(cls, json_data: dict) -> GradeData:
        """Create GradeData from JSON dict."""
        return cls(
            total=json_data["total"],
            a=json_data["a"],
            ab=json_data["ab"],
            b=json_data["b"],
            bc=json_data["bc"],
            c=json_data["c"],
            d=json_data["d"],
            f=json_data["f"],
            satisfactory=json_data["satisfactory"],
            unsatisfactory=json_data["unsatisfactory"],
            credit=json_data["credit"],
            no_credit=json_data["no_credit"],
            passed=json_data["passed"],
            incomplete=json_data["incomplete"],
            no_work=json_data["no_work"],
            not_reported=json_data["not_reported"],
            other=json_data["other"],
            instructors=json_data.get("instructors"),
        )

    def to_dict(self) -> dict:
        """Convert to dict for JSON serialization."""
        return self.model_dump()


class MeetingLocation(_MeetingLocationBase):
    """Extended MeetingLocation with deduplication cache."""

    model_config = ConfigDict(frozen=False)  # Allow mutation for capacity updates

    # Class-level dict to track all unique meeting locations for O(1) lookup
    _all_locations: ClassVar[dict[tuple, "MeetingLocation"]] = {}

    @classmethod
    def get_or_create_with_capacity(
        cls,
        building: str | None,
        room: str | None,
        coordinates: tuple[float, float] | None,
        class_capacity: int | None,
    ) -> MeetingLocation:
        """
        Get existing MeetingLocation or create new one, updating max capacity.

        Args:
            building: Building name
            room: Room identifier
            coordinates: Tuple of (latitude, longitude)
            class_capacity: Current class capacity (used to estimate room capacity)

        Returns:
            MeetingLocation instance with updated max capacity
        """
        location_key = (building, room, coordinates)

        if location_key in cls._all_locations:
            existing_location = cls._all_locations[location_key]
            # Update capacity to maximum seen so far
            if existing_location.capacity is None or (
                class_capacity is not None
                and class_capacity > existing_location.capacity
            ):
                # Create new instance with updated capacity (Pydantic models are immutable by default)
                updated = cls(
                    building=existing_location.building,
                    room=existing_location.room,
                    coordinates=existing_location.coordinates,
                    capacity=class_capacity,
                )
                cls._all_locations[location_key] = updated
                return updated
            return existing_location
        else:
            new_location = cls(
                building=building,
                room=room,
                coordinates=coordinates,
                capacity=class_capacity,
            )
            cls._all_locations[location_key] = new_location
            return new_location

    @classmethod
    def from_json(cls, data: dict) -> MeetingLocation:
        """Create MeetingLocation from JSON dict."""
        coordinates = data.get("coordinates")
        return cls.get_or_create_with_capacity(
            building=data.get("building"),
            room=data.get("room"),
            coordinates=tuple(coordinates) if coordinates else None,
            class_capacity=data.get("capacity"),
        )

    def to_dict(self) -> dict:
        """Convert to dict for JSON serialization."""
        return self.model_dump()


class Meeting(_MeetingBase):
    """Extended Meeting with factory methods."""

    @classmethod
    def from_json(cls, data: dict) -> Meeting:
        """Create Meeting from JSON dict."""
        course_reference = None
        if data.get("course_reference"):
            from schemas.course import CourseReference

            course_reference = CourseReference.model_validate(data["course_reference"])

        location = None
        if data.get("location"):
            location = MeetingLocation.from_json(data["location"])

        return cls(
            name=data["name"],
            type=data["type"],
            start_time=data.get("start_time"),
            end_time=data.get("end_time"),
            location=location,
            current_enrollment=data.get("current_enrollment"),
            instructors=data.get("instructors", []),
            course_reference=course_reference,
        )

    def to_dict(self) -> dict:
        """Convert to dict for JSON serialization."""
        return self.model_dump()


class EnrollmentData(_EnrollmentDataBase):
    """Extended EnrollmentData with factory methods."""

    @classmethod
    def from_json(cls, data: dict) -> EnrollmentData:
        """Create EnrollmentData from JSON dict."""
        school = None
        if data.get("school"):
            school = School.model_validate(data["school"])

        credit_count = data.get("credit_count", [0, 0])

        return cls(
            school=school,
            last_taught_term=data.get("last_taught_term"),
            typically_offered=data.get("typically_offered"),
            credit_count=(credit_count[0], credit_count[1]),
            general_education=data.get("general_education", False),
            ethnics_studies=data.get("ethnics_studies", False),
            instructors=data.get("instructors", {}),
        )

    @classmethod
    def from_enrollment(cls, data: dict, terms: dict[int, str]) -> EnrollmentData:
        """Create EnrollmentData from enrollment API response."""
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

    def to_dict(self) -> dict:
        """Convert to dict for JSON serialization."""
        return self.model_dump()


class MadgradesData:
    """Wrapper for Madgrades API data."""

    def __init__(self, cumulative: GradeData, by_term: dict[str, GradeData]):
        self.cumulative = cumulative
        self.by_term = by_term

    @classmethod
    async def from_madgrades_async(
        cls,
        session,
        url: str,
        madgrades_api_key: str,
        current_page: int,
        attempts: int = 3,
    ) -> MadgradesData:
        """Fetch grade data from Madgrades API."""
        auth_header = {"Authorization": f"Token token={madgrades_api_key}"}

        try:
            async with session.get(url, headers=auth_header) as response:
                data = await response.json()
        except (JSONDecodeError, Exception) as e:
            if attempts > 0:
                logger.debug(
                    f"Failed to fetch Madgrades data from {url}: {e}. "
                    f"Attempting {attempts} more times..."
                )
                await asyncio.sleep(1)
                return await cls.from_madgrades_async(
                    session, url, madgrades_api_key, current_page, attempts - 1
                )
            logger.error(f"Failed to fetch Madgrades data from {url}: {e}")
            raise

        cumulative = GradeData.from_madgrades(data["cumulative"])
        course_offerings = data["courseOfferings"]

        by_term = {}
        for offering in course_offerings:
            term_code = str(offering["termCode"])
            grade_data = GradeData.from_madgrades(offering["cumulative"])

            instructors = set()
            sections = offering["sections"]

            for section in sections:
                for instructor in section["instructors"]:
                    name = instructor["name"]
                    if name:
                        instructors.add(name)

            # Update instructors on the grade data
            grade_data = GradeData(
                **{**grade_data.model_dump(), "instructors": list(instructors)}
            )

            by_term[term_code] = grade_data

        return MadgradesData(cumulative=cumulative, by_term=by_term)
