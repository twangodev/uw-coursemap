"""Grade data Pydantic models."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class GradeData(BaseModel):
    """Grade distribution data for a course or instructor."""

    model_config = ConfigDict(
        populate_by_name=True,
        # Allow set -> list conversion during serialization
        ser_json_typing_mode="always",
    )

    total: int
    a: int
    ab: int
    b: int
    bc: int
    c: int
    d: int
    f: int
    satisfactory: int
    unsatisfactory: int
    credit: int
    no_credit: int
    passed: int
    incomplete: int
    no_work: int
    not_reported: int
    other: int
    instructors: list[str] | None = None

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

        merged_instructors: list[str] | None = None
        if self.instructors is not None and other.instructors is not None:
            merged_instructors = list(set(self.instructors) | set(other.instructors))
        elif self.instructors is not None:
            merged_instructors = self.instructors
        elif other.instructors is not None:
            merged_instructors = other.instructors

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
