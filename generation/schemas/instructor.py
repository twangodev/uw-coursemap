"""Instructor-related Pydantic models."""

from __future__ import annotations


from pydantic import BaseModel, ConfigDict, field_serializer

from schemas.course import CourseReference
from schemas.grades import GradeData


class MandatoryAttendance(BaseModel):
    """Mandatory attendance statistics from RMP."""

    yes: int = 0
    no: int = 0
    neither: int = 0
    total: int = 0


class RatingsDistribution(BaseModel):
    """Rating distribution from RMP."""

    r1: int = 0
    r2: int = 0
    r3: int = 0
    r4: int = 0
    r5: int = 0
    total: int = 0


class Rating(BaseModel):
    """Individual rating from RMP."""

    comment: str
    quality_rating: float
    difficulty_rating: float


class RMPData(BaseModel):
    """Rate My Professors data for an instructor."""

    id: str
    legacy_id: int
    average_rating: float | None = None
    average_difficulty: float | None = None
    num_ratings: int = 0
    would_take_again_percent: float | None = None
    mandatory_attendance: MandatoryAttendance | None = None
    ratings_distribution: RatingsDistribution | None = None
    ratings: list[Rating] = []

    @classmethod
    def from_rmp_data(cls, rmp_data: dict) -> RMPData:
        """Create RMPData from RMP GraphQL API response."""
        ratings = []
        for rating in rmp_data["ratings"]["edges"]:
            node = rating["node"]
            ratings.append(
                Rating(
                    comment=node["comment"],
                    quality_rating=node["qualityRating"],
                    difficulty_rating=node["difficultyRatingRounded"],
                )
            )

        # Convert mandatory_attendance dict to model if present
        mandatory_attendance = None
        if rmp_data.get("mandatoryAttendance"):
            ma = rmp_data["mandatoryAttendance"]
            mandatory_attendance = MandatoryAttendance(
                yes=ma.get("yes", 0),
                no=ma.get("no", 0),
                neither=ma.get("neither", 0),
                total=ma.get("total", 0),
            )

        # Convert ratings_distribution dict to model if present
        ratings_distribution = None
        if rmp_data.get("ratingsDistribution"):
            rd = rmp_data["ratingsDistribution"]
            ratings_distribution = RatingsDistribution(
                r1=rd.get("r1", 0),
                r2=rd.get("r2", 0),
                r3=rd.get("r3", 0),
                r4=rd.get("r4", 0),
                r5=rd.get("r5", 0),
                total=rd.get("total", 0),
            )

        return cls(
            id=rmp_data["id"],
            legacy_id=rmp_data["legacyId"],
            average_rating=rmp_data["avgRatingRounded"],
            average_difficulty=rmp_data["avgDifficultyRounded"],
            num_ratings=rmp_data["numRatings"],
            would_take_again_percent=rmp_data["wouldTakeAgainPercentRounded"],
            mandatory_attendance=mandatory_attendance,
            ratings_distribution=ratings_distribution,
            ratings=ratings,
        )


class FullInstructor(BaseModel):
    """Complete instructor information including RMP data."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str
    email: str | None = None
    rmp_data: RMPData | None = None
    position: str | None = None
    department: str | None = None
    credentials: str | None = None
    official_name: str | None = None
    courses_taught: list[CourseReference] | None = None
    cumulative_grade_data: GradeData | None = None

    @field_serializer("courses_taught")
    def serialize_courses_taught(
        self, courses: list[CourseReference] | None
    ) -> list[dict] | None:
        """Serialize course references to dicts."""
        if courses is None:
            return None
        result = []
        for course in courses:
            if hasattr(course, "model_dump"):
                result.append(course.model_dump())
            elif hasattr(course, "to_dict"):
                result.append(course.to_dict())
            else:
                result.append(course)
        return result
