import asyncio
import os
import re
import threading
from collections import defaultdict
from logging import Logger
from asyncio import Semaphore

import requests
from aiohttp import DummyCookieJar
from aiohttp_client_cache import CachedSession
from bs4 import BeautifulSoup
from diskcache import Cache
from nameparser import HumanName
from rapidfuzz import fuzz
from tqdm.asyncio import tqdm

from aio_cache import get_aio_cache
from course import Course
from enrollment import build_from_mega_query
from enrollment_data import GradeData
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

    def __init__(self, name, email, rmp_data, position, department, credentials, official_name, courses_taught = None, cumulative_grade_data: GradeData | None = None):
        self.name = name
        self.email = email
        self.rmp_data = rmp_data
        self.position = position
        self.department = department
        self.credentials = credentials
        self.official_name = official_name
        self.courses_taught = courses_taught
        self.cumulative_grade_data = cumulative_grade_data

    @classmethod
    def from_json(cls, json_data) -> "FullInstructor":
        cumulative_grade_data = json_data.get("cumulative_grade_data", None)
        if cumulative_grade_data:
            cumulative_grade_data = GradeData.from_json(cumulative_grade_data)

        courses_taught = json_data.get("courses_taught", None)
        if courses_taught:
            courses_taught = set(courses_taught)

        return FullInstructor(
            name=json_data["name"],
            email=json_data["email"],
            rmp_data=RMPData.from_json(json_data["rmp_data"]),
            position=json_data["position"],
            department=json_data["department"],
            credentials=json_data["credentials"],
            official_name=json_data["official_name"],
            courses_taught=courses_taught,
            cumulative_grade_data=cumulative_grade_data
        )

    def to_dict(self):
        return {
            "name": self.name,
            "email": self.email,
            "rmp_data": self.rmp_data.to_dict() if self.rmp_data else None,
            "position": self.position,
            "department": self.department,
            "credentials": self.credentials,
            "official_name": self.official_name,
            "courses_taught": list(self.courses_taught) if self.courses_taught else None,
            "cumulative_grade_data": self.cumulative_grade_data.to_dict() if self.cumulative_grade_data else None
        }


def produce_query(instructor_name):
    return {
        "query": {
            "text": instructor_name,
            "schoolID": "U2Nob29sLTE4NDE4",  # UW-Madison
        }
    }


mock_user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"

async def get_rating(name: str, api_key: str, logger: Logger, session, attempts: int = 10, rate_limited_count: int = 0, disable_cache=False):
    auth_header = {
        "Authorization": f"Basic {api_key}",
        "User-Agent": mock_user_agent
    }
    payload = {"query": graph_ql_query, "variables": produce_query(name)}

    try:
        if disable_cache:
            async with session.disabled():
                async with session.post(url=rmp_graphql_url, headers=auth_header, json=payload) as response:
                    data = await response.json()
        else:
            async with session.post(url=rmp_graphql_url, headers=auth_header, json=payload) as response:
                data = await response.json()

        if response.status == 429:
            backoff = min(30, 2 ** rate_limited_count)
            logger.debug(f"Rate limited, retrying after {backoff} seconds.")
            await asyncio.sleep(backoff)
            return await get_rating(name, api_key, logger, session, attempts, rate_limited_count + 1, disable_cache)

        if data.get("errors"):
            raise Exception(f"RMP API returned errors with status code {response.status}: {data['errors']}")

    except Exception as e:
        if attempts > 0:
            logger.debug(f"Failed to fetch or decode JSON response for {name} with {attempts} remaining attempts: {e}")
            await asyncio.sleep(1)
            return await get_rating(name, api_key, logger, session, attempts - 1, rate_limited_count, True)
        logger.error(f"Failed to fetch or decode JSON response for {name}: {e}")
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

def scrape_rmp_api_key(logger):
    response = requests.get(rmp_url, headers={"User-Agent": "Mozilla/5.0"}) # Some sites require a user-agent to avoid blocking

    match = re.search(r'"REACT_APP_GRAPHQL_AUTH"\s*:\s*"([^"]+)"', response.text)
    if match:
        graphql_auth = match.group(1)
    else :
        logger.error("Failed to scrape the RMP API key from the response.")
        logger.debug(response.text)
        raise RuntimeError("Failed to scrape the RMP API key from the response.")

    logger.info(f"Scraped RMP API key: {graphql_auth}")

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


_caches: dict[str, Cache] = {}
_caches_lock = threading.Lock()

def get_match_cache(cache_dir: str) -> Cache:
    # build one canonical directory for your cache
    path = os.path.abspath(os.path.join(cache_dir, "name_cache"))
    os.makedirs(path, exist_ok=True)

    with _caches_lock:
        cache = _caches.get(path)
        if cache is None:
            cache = Cache(path)
            _caches[path] = cache
    return cache

null_sentinel = object()

def match_name(student_name, official_names, cache_dir, query_cache_group, threshold=80):

    cache = get_match_cache(cache_dir)
    cache_key = f"{query_cache_group}:{student_name.strip().upper()}"

    cache_entry = cache.get(cache_key, default=null_sentinel)
    if cache_entry is not null_sentinel:
        return cache_entry

    # Parse and normalize the student name.
    student_parsed = HumanName(student_name)
    student_first = student_parsed.first.upper().strip()
    student_last = student_parsed.last.upper().strip()

    best_match = None
    best_score = 0

    for candidate in official_names:
        candidate_parsed = HumanName(candidate)
        candidate_first = candidate_parsed.first.upper().strip()
        candidate_last = candidate_parsed.last.upper().strip()

        # Filter: if the last names don't match exactly, skip this candidate.
        if student_last != candidate_last:
            continue

        # Use fuzzy matching on the first name.
        score = fuzz.token_set_ratio(student_first, candidate_first)
        if score > best_score:
            best_score = score
            best_match = candidate

    result = best_match if best_score >= threshold else None

    cache.set(cache_key, result)
    return result

def generate_instructor_merge_diff(
        instructor: str,
        instructors: dict[str, str | None],
        appearances: dict[str, list[tuple[Course.Reference, str]]],
        cache_dir: str
) -> list[dict]:
    diffs = []
    match = match_name(instructor, set(instructors.keys()), cache_dir, "instructors")

    if match and match != instructor:
        # only iterate the courses/terms where this instructor actually shows up
        for course_ref, term in appearances.get(instructor, []):
            diffs.append({
                "type":       "replace_in_course",
                "course_ref": course_ref,
                "term":       term,
                "old":        instructor,
                "new":        match,
            })
    elif match is None:
        diffs.append({
            "type":       "add_instructor",
            "instructor": instructor,
        })

    return diffs


async def merge_instructors(additional_instructors, instructors, course_ref_to_course, cache_dir):

    instructor_appearances: dict[str, list[tuple[Course.Reference, str]]] = defaultdict(list)
    for course_ref, course in course_ref_to_course.items():
        for term, term_data in course.term_data.items():
            if term_data.grade_data:
                for instr in term_data.grade_data.instructors:
                    instructor_appearances[instr].append((course_ref, term))

    tasks = [
        asyncio.to_thread(
            generate_instructor_merge_diff,
            inst,
            instructors,
            instructor_appearances,
            cache_dir,
        )
        for inst in additional_instructors
    ]

    all_diffs = await tqdm.gather(
        *tasks,
        desc="Generate Instructor Diff",
        unit="instructor"
    )

    for difflist in tqdm(all_diffs, desc="Merge Instructor Diff", unit="diff"):
        for diff in difflist:
            if diff["type"] == "add_instructor":
                instructors[diff["instructor"]] = None
            elif diff["type"] == "replace_in_course":
                cr = diff["course_ref"]
                term = diff["term"]
                gd = course_ref_to_course[cr].term_data[term].grade_data
                gd.instructors.remove(diff["old"])
                gd.instructors.add(diff["new"])

async def sem_get_rating(sem: asyncio.Semaphore, name, api_key, logger, session):
    async with sem:
        return await get_rating(name, api_key, logger, session)

async def get_ratings(instructors: dict[str, str | None], api_key: str, course_ref_to_course: dict[Course.Reference, Course], cache_dir, logger: Logger):
    faculty = get_faculty()  # Assuming these functions are fast/synchronous.

    additional_instructors = set()

    # Gather all instructors from the course data.
    for course in course_ref_to_course.values():
        for term_data in course.term_data.values():
            if not term_data or not term_data.grade_data or not term_data.grade_data.instructors:
                continue
            for instructor in term_data.grade_data.instructors:
                if instructor:
                    additional_instructors.add(instructor)

    await merge_instructors(additional_instructors, instructors, course_ref_to_course, cache_dir)

    instructor_data = {}
    total = len(instructors)
    with_ratings = 0

    logger.info(f"Fetching ratings for {total} instructors...")

    async with CachedSession(cache=get_aio_cache(), cookie_jar=DummyCookieJar()) as session:
        semaphore = Semaphore(10)
        tasks = []
        names_emails = list(instructors.items())
        for i, (name, email) in enumerate(names_emails):
            logger.debug(f"Fetching rating for {name} ({i * 100 / total:.2f}%).")
            # Create a task to get the rating for each instructor
            tasks.append(sem_get_rating(semaphore, name, api_key, logger, session))

        # Run all rating requests concurrently
        ratings = await tqdm.gather(*tasks, desc="RMP Query", unit="instructor")

        faculty_names = set(faculty.keys())

        async def _process_one(name_email, rating):
            instructor_name, instructor_email = name_email
            match = await asyncio.to_thread(match_name, instructor_name, faculty_names, cache_dir, "rmp")

            if match:
                position, department, credentials = faculty[match]
                logger.debug(f"Matched {instructor_name} to {match} ({position}, {department}, {credentials})")
            else:
                position = department = credentials = None

            inst = FullInstructor(
                name=instructor_name,
                email=instructor_email,
                rmp_data=rating,
                position=position,
                department=department,
                credentials=credentials,
                official_name=match
            )
            return instructor_name, inst, bool(rating)

        process_tasks = [
            _process_one(ne, r)
            for ne, r in zip(names_emails, ratings)
        ]

        # run them all in parallel, with a tqdm progress bar
        results = await tqdm.gather(
            *process_tasks,
            desc="Process Ratings",
            unit="instructor",
        )

        # collect your results
        for name, inst, had_rating in results:
            if had_rating:
                with_ratings += 1
            instructor_data[name] = inst

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
            selected_term=str(term),
            term_name=terms[term],
            terms=terms,
            course_ref_to_course=course_ref_to_course,
            logger=logger
        )
        for term in sorted_terms
    ]
    # Run all tasks concurrently
    results = await tqdm.gather(*tasks, desc="Term Query", unit="term")
    # Merge dictionaries; later ones override earlier ones for duplicate keys
    for term, emails in zip(sorted_terms, results):
        combined_emails.update(emails)
    return combined_emails