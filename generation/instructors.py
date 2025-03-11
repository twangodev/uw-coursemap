import asyncio
import re
from json import JSONDecodeError
from logging import Logger

import aiohttp
import requests
from bs4 import BeautifulSoup

from enrollment import build_from_mega_query
from json_serializable import JsonSerializable

faculty_url = "https://guide.wisc.edu/faculty/"

rmp_url = "https://www.ratemyprofessors.com/"
rmp_graphql_url = "https://www.ratemyprofessors.com/graphql"

graph_ql_query = """
query NewSearchTeachersQuery($query: TeacherSearchQuery!) {
	newSearch {
		teachers(query: $query, first: 50) {
			didFallback
			edges {
				cursor
				node {
					id
					legacyId
					firstName
					lastName
					school {
						legacyId
						name
						id
					}
					avgRatingRounded
					avgDifficultyRounded
					numRatings
					wouldTakeAgainPercentRounded
					mandatoryAttendance {
						yes
						no
						neither
						total
					}
					ratingsDistribution {
						r1
						r2
						r3
						r4
						r5
						total
					}
					ratings(first: 100) {
						edges {
							node {
								comment
								qualityRating
								difficultyRatingRounded
							}
						}
					}
				}
			}
		}
	}
}
"""


class RMPData(JsonSerializable):

    def __init__(self, id, legacy_id, average_rating, average_difficulty, num_ratings, would_take_again_percent,
                 mandatory_attendance, ratings_distribution, ratings):
        self.id = id
        self.legacy_id = legacy_id
        self.average_rating = average_rating
        self.average_difficulty = average_difficulty
        self.num_ratings = num_ratings
        self.would_take_again_percent = would_take_again_percent
        self.mandatory_attendance = mandatory_attendance
        self.ratings_distribution = ratings_distribution
        self.ratings = ratings

    @classmethod
    def from_json(cls, json_data):
        if not json_data:
            return None
        return RMPData(
            id=json_data["id"],
            legacy_id=json_data["legacy_id"],
            average_rating=json_data["average_rating"],
            average_difficulty=json_data["average_difficulty"],
            num_ratings=json_data["num_ratings"],
            would_take_again_percent=json_data["would_take_again_percent"],
            mandatory_attendance=json_data["mandatory_attendance"],
            ratings_distribution=json_data["ratings_distribution"],
            ratings=json_data["ratings"]
        )

    @classmethod
    def from_rmp_data(cls, rmp_data) -> "RMPData":
        id = rmp_data["id"]
        legacy_id = rmp_data["legacyId"]
        average_rating = rmp_data["avgRatingRounded"]
        average_difficulty = rmp_data["avgDifficultyRounded"]
        num_ratings = rmp_data["numRatings"]
        would_take_again_percent = rmp_data["wouldTakeAgainPercentRounded"]
        mandatory_attendance = rmp_data["mandatoryAttendance"]
        ratings_distribution = rmp_data["ratingsDistribution"]

        ratings = []
        for rating in rmp_data["ratings"]["edges"]:
            node = rating["node"]
            ratings.append({
                "comment": node["comment"],
                "quality_rating": node["qualityRating"],
                "difficulty_rating": node["difficultyRatingRounded"]
            })

        return RMPData(
            id=id,
            legacy_id=legacy_id,
            average_rating=average_rating,
            average_difficulty=average_difficulty,
            num_ratings=num_ratings,
            would_take_again_percent=would_take_again_percent,
            mandatory_attendance=mandatory_attendance,
            ratings_distribution=ratings_distribution,
            ratings=ratings
        )

    def to_dict(self):
        return {
            "id": self.id,
            "legacy_id": self.legacy_id,
            "average_rating": self.average_rating,
            "average_difficulty": self.average_difficulty,
            "num_ratings": self.num_ratings,
            "would_take_again_percent": self.would_take_again_percent,
            "mandatory_attendance": self.mandatory_attendance,
            "ratings_distribution": self.ratings_distribution,
            "ratings": self.ratings
        }


class FullInstructor(JsonSerializable):

    def __init__(self, name, email, rmp_data, position, department, credentials, official_name):
        self.name = name
        self.email = email
        self.rmp_data = rmp_data
        self.position = position
        self.department = department
        self.credentials = credentials
        self.official_name = official_name

    @classmethod
    def from_json(cls, json_data) -> "FullInstructor":
        return FullInstructor(
            name=json_data["name"],
            email=json_data["email"],
            rmp_data=RMPData.from_json(json_data["rmp_data"]),
            position=json_data["position"],
            department=json_data["department"],
            credentials=json_data["credentials"],
            official_name=json_data["official_name"]
        )

    def to_dict(self):
        return {
            "name": self.name,
            "email": self.email,
            "rmp_data": self.rmp_data.to_dict() if self.rmp_data else None,
            "position": self.position,
            "department": self.department,
            "credentials": self.credentials,
            "official_name": self.official_name
        }


def produce_query(instructor_name):
    return {
        "query": {
            "text": instructor_name,
            "schoolID": "U2Nob29sLTE4NDE4",  # UW-Madison
        }
    }


async def get_rating(name: str, api_key: str, logger: Logger, session: aiohttp.ClientSession, attempts: int = 3):
    auth_header = {"Authorization": f"Basic {api_key}"}
    payload = {"query": graph_ql_query, "variables": produce_query(name)}

    try:
        async with session.post(url=rmp_graphql_url, headers=auth_header, json=payload) as response:
            data = await response.json()
    except (aiohttp.ClientError, JSONDecodeError) as e:
        logger.error(f"Failed to fetch or decode JSON response for {name}: {e}")
        if attempts > 0:
            logger.info(f"Retrying {attempts} more times for {name}...")
            await asyncio.sleep(1)
            return await get_rating(name, api_key, logger, session, attempts - 1)
        return None

    # Parse the results to find a matching teacher
    results = data["data"]["newSearch"]["teachers"]["edges"]
    for item in results:
        result = item["node"]
        # Simple matching: check if both first and last names appear in the name string
        if result["firstName"].lower() in name.lower() and result["lastName"].lower() in name.lower():
            return RMPData.from_rmp_data(result)

    logger.debug(f"Failed to find rating for {name}")
    return None


def scrape_api_key():
    response = requests.get(rmp_url)

    match = re.search(r'"REACT_APP_GRAPHQL_AUTH"\s*:\s*"([^"]+)"', response.text)
    graphql_auth = match.group(1)

    return graphql_auth


def get_faculty():
    response = requests.get(faculty_url)

    soup = BeautifulSoup(response.content, "html.parser")
    uw_people_lists = soup.find_all("ul", class_="uw-people")

    faculty = {}

    for ul in uw_people_lists:
        for li in ul.find_all("li"):
            name = li.find("span", class_="faculty-name").text if li.find("span", class_="faculty-name") else None

            if not name:
                continue

            details = li.get_text(separator="\n").split("\n")
            position = details[1] if len(details) > 1 else None
            department = details[2] if len(details) > 2 else None
            credentials = details[3] if len(details) > 3 else None

            faculty[name] = (position, department, credentials)

    return faculty


def match_name(student_name, official_names):
    """
    Matches a student-provided name to an official name based on last name priority.

    Args:
        student_name (str): The name given by the student.
        official_names (set of str): The list of official names.

    Returns:
        str: The matched official name or None if no match is found.
    """
    student_last_name = student_name.split()[-1].upper()
    matches = [official_name for official_name in official_names if student_last_name in official_name.upper()]

    if len(matches) == 1:
        return matches[0]

    # If multiple matches, attempt further refinement (e.g., first name matching)
    student_first_name = student_name.split()[0].upper() if len(student_name.split()) > 1 else ""
    for match in matches:
        official_first_name = match.split(',')[1].strip().split()[0].upper() if ',' in match else ""
        if student_first_name == official_first_name:
            return match

    return matches[0] if matches else None


async def get_ratings(instructors: dict[str, str], logger: Logger):
    faculty = get_faculty()  # Assuming these functions are fast/synchronous.
    api_key = scrape_api_key()

    instructor_data = {}
    total = len(instructors)
    with_ratings = 0

    logger.info(f"Fetching ratings for {total} instructors...")

    async with aiohttp.ClientSession() as session:
        tasks = []
        names_emails = list(instructors.items())
        for i, (name, email) in enumerate(names_emails):
            logger.debug(f"Fetching rating for {name} ({i * 100 / total:.2f}%).")
            # Create a task to get the rating for each instructor
            tasks.append(get_rating(name, api_key, logger, session))

        # Run all rating requests concurrently
        ratings = await asyncio.gather(*tasks)

        # Process results
        for (name, email), rating in zip(names_emails, ratings):
            if rating:
                with_ratings += 1

            match = match_name(name, set(faculty.keys()))
            position, department, credentials = None, None, None
            if match:
                position, department, credentials = faculty[match]
                logger.debug(f"Matched {name} to {match} ({position}, {department}, {credentials})")

            instructor_data[name] = FullInstructor(
                name=name,
                email=email,
                rmp_data=rating,
                position=position,
                department=department,
                credentials=credentials,
                official_name=match
            )

    logger.info(
        f"Found instructor_data for {with_ratings} out of {total} instructors ({with_ratings * 100 / total:.2f}%).")
    return instructor_data

async def gather_instructor_emails(terms, course_ref_to_course, logger):
    combined_emails = {}
    # sort terms so that later (i.e. 'larger') keys override earlier ones
    sorted_terms = sorted(terms.keys())
    # Create a list of tasks, one per term
    tasks = [
        build_from_mega_query(
            selected_term=term,
            terms=terms,
            course_ref_to_course=course_ref_to_course,
            logger=logger
        )
        for term in sorted_terms
    ]
    # Run all tasks concurrently
    results = await asyncio.gather(*tasks)
    # Merge dictionaries; later ones override earlier ones for duplicate keys
    for term, emails in zip(sorted_terms, results):
        combined_emails.update(emails)
    return combined_emails