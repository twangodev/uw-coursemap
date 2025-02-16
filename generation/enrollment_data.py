from json_serializable import JsonSerializable
from safe_parse import safe_int


class EnrollmentData(JsonSerializable):

    class School(JsonSerializable):

        def __init__(self, name, abbreviation, url):
            self.name = name
            self.abbreviation = abbreviation
            self.url = url

        @classmethod
        def from_json(cls, data) -> 'EnrollmentData.School':
            return EnrollmentData.School(
                name=data["name"],
                abbreviation=data["abbreviation"],
                url=data["url"]
            )

        def to_dict(self) -> dict:
            return {
                "name": self.name,
                "abbreviation": self.abbreviation,
                "url": self.url
            }

        @classmethod
        def from_enrollment(cls, data) -> 'EnrollmentData.School':
            return EnrollmentData.School(
                name=data["shortDescription"],
                abbreviation=data["academicOrgCode"],
                url=data["schoolCollegeURI"]
            )

        def __str__(self):
            return self.name

        def __eq__(self, other):
            return self.name == other.name and self.abbreviation == other.abbreviation and self.url == other.url

    def __init__(self, school, last_taught_term, typically_offered: str, credit_count: tuple[int, int], general_education: bool, ethnics_studies: bool, instructors):
        self.school = school
        self.last_taught_term = last_taught_term
        self.typically_offered = typically_offered
        self.credit_count = credit_count
        self.general_education = general_education
        self.ethnics_studies = ethnics_studies
        self.instructors = instructors

    @classmethod
    def from_json(cls, data) -> 'EnrollmentData':
        return EnrollmentData(
            school=EnrollmentData.School.from_json(data["school"]),
            last_taught_term=data["last_taught_term"],
            typically_offered=data["typically_offered"],
            credit_count=(data["credit_count"][0], data["credit_count"][1]),
            general_education=data["general_education"],
            ethnics_studies=data["ethnics_studies"],
            instructors=data["instructors"]
        )

    @classmethod
    def from_enrollment(cls, data, terms) -> 'EnrollmentData':
        last_taught_term_code = safe_int(data["lastTaught"])
        last_taught_term = None
        if last_taught_term_code and last_taught_term_code in terms:
            last_taught_term = terms[last_taught_term_code]
        return EnrollmentData(
            school=EnrollmentData.School.from_enrollment(data["subject"]["schoolCollege"]),
            last_taught_term=last_taught_term,
            typically_offered=data["typicallyOffered"],
            credit_count=(data["minimumCredits"], data["maximumCredits"]),
            general_education=data["generalEd"] is not None,
            ethnics_studies=data["ethnicStudies"] is not None,
            instructors={}
        )

    def to_dict(self) -> dict:
        return {
            "school": self.school.to_dict(),
            "last_taught_term": self.last_taught_term,
            "typically_offered": self.typically_offered,
            "credit_count": [self.credit_count[0], self.credit_count[1]],
            "general_education": self.general_education,
            "ethnics_studies": self.ethnics_studies,
            "instructors": self.instructors
        }