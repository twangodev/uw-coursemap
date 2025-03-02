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

def search_courses(es: Elasticsearch, search_term):

    # Build the Elasticsearch query; this example uses a match query on course_title
    numeric_part = "".join(re.findall(r"\d+", search_term))
    word_part = "".join(re.findall(r"\D+", search_term))

    es_query = {
        "query": {
            "bool": {
                "must": [],  # `must` ensures course_number is strictly required
                "should": [
                    {"match": {"course_title": {"query": word_part, "fuzziness": "AUTO"}}},
                    {"match": {"course_reference": {"query": search_term, "fuzziness": "AUTO"}}},
                    {"match": {"subjects": {"query": word_part, "fuzziness": "AUTO"}}},
                    {"match": {"departments": {"query": word_part, "fuzziness": "AUTO"}}},
                    {"wildcard": {"course_title": f"*{word_part}*"}},
                    {"wildcard": {"course_reference": f"*{search_term}*"}},
                    {"wildcard": {"subjects": f"*{word_part}*"}},
                    {"wildcard": {"departments": f"*{word_part}*"}},
                ],
                "minimum_should_match": 1  # At least one of these should match
            }
        },
        "size": 10
    }

    # If numeric part exists, add a strict term match for course_number (must match)
    if numeric_part:
        es_query["query"]["bool"]["must"].append(
            {"term": {"course_number": int(numeric_part)}}
        )

    # Execute the search on the 'courses' index
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

