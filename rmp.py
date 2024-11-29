import logging
import re
from json import JSONDecodeError
from logging import Logger

import requests
from bs4 import BeautifulSoup

from json_serializable import JsonSerializable

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
					ratings(first: 10) {
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

    def __init__(self, id, legacy_id, average_rating, average_difficulty, num_ratings, would_take_again_percent, mandatory_attendance, ratings_distribution, ratings):
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
    def from_json(cls, json_data) -> "RMPData":
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

def produce_query(instructor_name):
    return {
        "query": {
            "text": instructor_name,
            "schoolID": "U2Nob29sLTE4NDE4", # UW-Madison
        }
    }

def get_rating(name, api_key, logger: Logger):
    auth_header = { "Authorization": f"Basic {api_key}" }
    response = requests.post(
        url=rmp_graphql_url,
        headers=auth_header,
        json={"query": graph_ql_query, "variables": produce_query(name)}
    )
    try:
        data = response.json()
    except JSONDecodeError:
        logger.error(f"Failed to decode JSON response: {response.text}")
        return None

    results = data["data"]["newSearch"]["teachers"]["edges"]

    for result in results:
        result = result["node"]

        if result["firstName"].lower() in name.lower() and result["lastName"].lower() in name.lower():
            return RMPData.from_rmp_data(result)

    logger.debug(f"Failed to find rating for {name}")
    return None

def scrape_api_key():
    response = requests.get(rmp_url)

    match = re.search(r'"REACT_APP_GRAPHQL_AUTH"\s*:\s*"([^"]+)"', response.text)
    graphql_auth = match.group(1)

    return graphql_auth

def get_ratings(instructors, stats, logger: Logger):
    api_key = scrape_api_key()

    ratings = {}
    total = len(instructors)
    with_ratings = 0
    for i, instructor in enumerate(instructors):
        logger.info(f"Fetching rating for {instructor} ({i * 100 / total:.2f}%).")
        rating = get_rating(instructor, api_key, logger)

        if rating:
            with_ratings += 1

        ratings[instructor] = rating

    logger.info(f"Found ratings for {with_ratings} out of {total} instructors ({with_ratings * 100 / total:.2f}%).")

    stats["instructors"] = total
    stats["instructors_with_ratings"] = with_ratings

    return ratings


