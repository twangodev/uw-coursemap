from logging import Logger
import re

from elasticsearch import helpers, Elasticsearch

from data import normalize_text

def generate_variations(subject_name: str, abbreviation: str):
    """
    Generate variations for a subject name. Variations include:
      - Original subject name
      - Provided abbreviation
      - Subject name without punctuation
      - Acronym (first letters of each word)
    """
    variations = set()
    subject_name = subject_name.strip()
    abbreviation = abbreviation.strip()

    # Variation 1: Original subject name
    variations.add(subject_name)

    # Variation 2: Abbreviation
    variations.add(abbreviation)

    # Variation 3: Subject name with punctuation removed
    no_punct_name = re.sub(r"[^\w\s]", "", subject_name)
    no_punct_abbre = re.sub(r"[^\w\s]", "", abbreviation)
    variations.add(no_punct_name)
    variations.add(no_punct_abbre)

    # Variation 4: Acronym from first letters of each word
    words = subject_name.split()
    if len(words) > 1:
        acronym = "".join(word[0].upper() for word in words)
        variations.add(acronym)
    return list(variations)

def load_subjects(es: Elasticsearch, subjects: dict | None, logger: Logger | None = None):
    """
    Index subjects into Elasticsearch.
    Generates normalized fields for both the subject name and abbreviation, plus variations.
    """
    if (subjects is None) or (len(subjects) == 0):
        if logger:
            logger.warning("No subjects to load into Elasticsearch.")
        return

    settings = {
        "settings": {
            "analysis": {
                "filter": {
                    "subject_synonyms": {
                        "type": "synonym_graph",
                        "updateable": True,
                        "synonyms": []
                    }
                },
                "analyzer": {
                    "subject_analyzer": {
                        "type": "custom",
                        "tokenizer": "standard",
                        "char_filter": [
                            {
                                "type": "pattern_replace",
                                "pattern": "-&",
                                # Note: modifying length of string may affect highlighting in search results
                                "replacement": "",
                            }
                        ],
                        "filter": [
                            "asciifolding",  
                            "lowercase",
                            "subject_synonyms",
                            "english_stop"
                        ]
                    }
                }
            }
        },
        "mappings": {
            "properties": {
                "id": { "type": "keyword" },
                "variations": { 
                    "type": "text", # type is specified as text, but it is intended to be a list of strings
                    "analyzer": "subject_analyzer",     
                    "search_analyzer": "subject_analyzer"
                }
            }
        }
    }

    es.indices.delete(index="subjects", ignore_unavailable=True)
    resp = es.indices.create(index="subjects", body=settings)
    
    if logger:
        logger.debug(f"Index exists: {resp}")

    actions = []

    for subject_id, subject_name in subjects.items():
        subject_id = normalize_text(subject_id)
        subject_name = normalize_text(subject_name)
        action = {
            "_index": "subjects",
            "_id": subject_id,
            "_source": {
                # strings are normalized by the analyzer when indexed
                "id": subject_id,
                "variations": generate_variations(subject_name, subject_id),
            }
        }
        actions.append(action)

    if logger:
        logger.info(f"Indexing {len(actions)} subjects into Elasticsearch.")
        logger.debug(f"All subjects: {str(subjects.keys())}")
        logger.debug(f"All subject names: {str(subjects.values())}")

    helpers.bulk(es, actions)

def search_subjects(es: Elasticsearch, search_term: str):
    search_term = normalize_text(search_term)
    es_query = {
        "query": {
            "match": {
                "variations": {
                    "query": search_term,
                },
                "fuzziness": "AUTO"
            }
        },
        "size": 5
    }
    results = es.search(index="subjects", body=es_query)
    hits = results.get("hits", {}).get("hits", [])
    return [
        {
            "subject_id": hit["_id"],
            "name": hit["_source"]["name"],
            "score": hit["_score"]
        }
        for hit in hits
    ]

def load_courses(es, courses):
    """
    Index courses into Elasticsearch.
    Adds normalized versions for key text fields.
    """
    es.indices.delete(index="courses", ignore_unavailable=True)
    es.indices.create(index="courses")

    actions = []
    for course_id, course_data in courses.items():
        # Original fields
        course_reference = course_data["course_reference"]
        course_title = course_data["course_title"]
        subjects_list = course_data["subjects"]
        departments_list = course_data["departments"]

        # Normalized versions
        normalized_course_reference = normalize_text(course_reference)
        normalized_course_title = normalize_text(course_title)
        normalized_subjects = [normalize_text(s) for s in subjects_list]
        normalized_departments = [normalize_text(d) for d in departments_list]

        course_doc = {
            **course_data,
            "course_reference_normalized": normalized_course_reference,
            "course_title_normalized": normalized_course_title,
            "subjects_normalized": normalized_subjects,
            "departments_normalized": normalized_departments
        }
        actions.append({
            "_index": "courses",
            "_id": course_id,
            "_source": course_doc
        })
    helpers.bulk(es, actions)

def search_courses(es: Elasticsearch, search_term: str):
    """
    Searches courses using both the original and normalized fields.
    Splits the search term into numeric and word parts to support queries like "COMP SCI 300".
    Instead of enforcing the numeric part, this version boosts courses that match the numeric component.
    """
    search_term = normalize_text(search_term)
    numeric_part = "".join(re.findall(r"\d+", search_term))
    word_part = "".join(re.findall(r"\D+", search_term)).strip()

    should_queries = []

    if word_part:
        should_queries.append({
            "multi_match": {
                "query": word_part,
                "fields": [
                    "course_title_normalized^5",
                    "course_reference_normalized^5",
                    "subjects_normalized^8",
                    "departments_normalized^3"
                ],
                "fuzziness": "AUTO"
            }
        })
        should_queries.extend([
            {"wildcard": {"course_title_normalized": f"*{word_part}*"}},
            {"wildcard": {"subjects_normalized": f"*{word_part}*"}},
            {"wildcard": {"departments_noramlized": f"*{word_part}*"}},
        ])

    # Wildcard matching on course_reference fields for the full search term.
    should_queries.append({
        "wildcard": {"course_reference_normalized": f"*{search_term}*"}
    })

    # If numeric part exists, add a boosted term query on course_number.
    if numeric_part:
        should_queries.append({
            "term": {
                "course_number": {
                    "value": int(numeric_part),
                    "boost": 7.5  # Boost factor can be adjusted as needed.
                }
            }
        })

    bool_query = {
        "must": [],
        "should": should_queries,
        "minimum_should_match": 1
    }

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
            "score": hit["_score"]
        }
        for hit in hits
    ]


def load_instructors(es, instructors):
    """
    Index instructors into Elasticsearch.
    Adds normalized versions for all text fields.
    """
    es.indices.delete(index="instructors", ignore_unavailable=True)
    es.indices.create(index="instructors")

    actions = []
    for instructor_id, instructor_data in instructors.items():
        name = instructor_data["name"]
        official_name = instructor_data["official_name"]
        email = instructor_data["email"]
        position = instructor_data["position"]
        department = instructor_data["department"]

        instructor_doc = {
            **instructor_data,
            "name_normalized": normalize_text(name),
            "official_name_normalized": normalize_text(official_name),
            "email_normalized": normalize_text(email),
            "position_normalized": normalize_text(position),
            "department_normalized": normalize_text(department),
        }
        actions.append({
            "_index": "instructors",
            "_id": instructor_id,
            "_source": instructor_doc
        })
    helpers.bulk(es, actions)

def search_instructors(es, search_term):
    search_term = normalize_text(search_term)
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
                                "department",
                                "name_normalized^10",
                                "official_name_normalized^2",
                                "email_normalized",
                                "position_normalized",
                                "department_normalized"
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
                                "department",
                                "name_normalized",
                                "official_name_normalized",
                                "email_normalized",
                                "position_normalized",
                                "department_normalized"
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
            "score": hit["_score"]
        }
        for hit in hits
    ]