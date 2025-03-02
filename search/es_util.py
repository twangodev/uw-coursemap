import re

from elasticsearch import helpers, Elasticsearch


def load_courses(es, courses):
    actions = [
        {
            "_index": "courses",
            "_id": course_id,
            "_source": course_data
        }
        for course_id, course_data in courses.items()
    ]

    helpers.bulk(es, actions)
def search_courses(es: Elasticsearch, search_term: str):
    # Sanitize input
    search_term = search_term.strip()
    numeric_part = "".join(re.findall(r"\d+", search_term))
    word_part = "".join(re.findall(r"\D+", search_term)).strip()

    should_queries = []

    if word_part:
        # Use multi_match to search in multiple fields with boosts
        should_queries.append({
            "multi_match": {
                "query": word_part,
                "fields": [
                    "course_title^3",      # Boost course_title
                    "course_reference^2",  # Moderate boost for course_reference
                    "subjects",
                    "departments"
                ],
                "fuzziness": "AUTO"
            }
        })
        # Add wildcard queries for partial matching on text fields
        should_queries.extend([
            {"wildcard": {"course_title": f"*{word_part}*"}},
            {"wildcard": {"subjects": f"*{word_part}*"}},
            {"wildcard": {"departments": f"*{word_part}*"}}
        ])

    # Always include a query on course_reference with the full search term
    should_queries.append({
        "wildcard": {"course_reference": f"*{search_term}*"}
    })

    bool_query = {
        "must": [],
        "should": should_queries,
        "minimum_should_match": 1
    }

    # If there's a numeric part, ensure course_number must match exactly
    if numeric_part:
        bool_query["must"].append({
            "term": {"course_number": int(numeric_part)}
        })

    es_query = {
        "query": {
            "bool": bool_query
        },
        "size": 10
    }

    results = es.search(index="courses", body=es_query)
    hits = results.get("hits", {}).get("hits", [])

    return [
        {
            "course_id": hit["_id"],
            "course_title": hit["_source"]["course_title"],
            "course_number": hit["_source"]["course_number"],
            "subjects": hit["_source"]["subjects"],
            "departments": hit["_source"]["departments"],
        }
        for hit in hits
    ]
def load_instructors(es, instructors):
    actions = [
        {
            "_index": "instructors",
            "_id": instructor_id,
            "_source": instructor_data
        }
        for instructor_id, instructor_data in instructors.items()
    ]

    helpers.bulk(es, actions)

def search_instructors(es, search_term):
    es_query = {
        "query": {
            "bool": {
                "should": [
                    {
                        "multi_match": {
                            "query": search_term,
                            "fields": [
                                "name^10",
                                "official_name^2",
                                "email",
                                "position",
                                "department"
                            ],
                            "fuzziness": "AUTO"
                        }
                    },
                    {
                        "query_string": {
                            "query": f"*{search_term}*",
                            "fields": [
                                "name",
                                "official_name",
                                "email",
                                "position",
                                "department"
                            ],
                            "analyze_wildcard": True
                        }
                    }
                ],
                "minimum_should_match": 1
            }
        },
        "size": 5
    }

    results = es.search(index="instructors", body=es_query)
    hits = results.get("hits", {}).get("hits", [])
    return [
        {
            "instructor_id": hit["_id"],
            "name": hit["_source"]["name"],
            "official_name": hit["_source"]["official_name"],
            "email": hit["_source"]["email"],
            "position": hit["_source"]["position"],
            "department": hit["_source"]["department"],
        }
        for hit in hits
    ]
