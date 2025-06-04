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
      - A shortened form (first 4 letters of each word)
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
    if words:
        acronym = "".join(word[0].upper() for word in words)
        variations.add(acronym)

    # Variation 5: Shortened form: first 4 letters (if available) for each word
    short_form_words = []
    for word in words:
        if len(word) > 4:
            short_form_words.append(word[:4].upper())
        else:
            short_form_words.append(word.upper())
    short_form = " ".join(short_form_words)
    variations.add(short_form)

    return list(variations)

def load_subjects(es: Elasticsearch, subjects: dict, logger: Logger | None = None):
    """
    Index subjects into Elasticsearch.
    Generates normalized fields for both the subject name and abbreviation, plus variations.
    """
    actions = [
        {
            "_index": "subjects",
            "_id": subject_id,
            "_source": {
                "abbreviation": subject_id,
                "abbreviation_normalized": normalize_text(subject_id),
                "name": subject_data,
                "name_normalized": normalize_text(subject_data),
                "variations": generate_variations(subject_data, subject_id),
                "variations_normalized": [normalize_text(v) for v in generate_variations(subject_data, subject_id)]
            }
        }
        for subject_id, subject_data in subjects.items()
    ]

    if logger:
        logger.info(f"Indexing {len(actions)} subjects into Elasticsearch.")
        logger.debug(f"All subjects: {str(subjects.keys())}")

    helpers.bulk(es, actions)

def search_subjects(es: Elasticsearch, search_term: str):
    search_term = normalize_text(search_term)
    es_query = {
        "query": {
            "multi_match": {
                "query": search_term,
                "fields": [
                    "name^20",
                    "abbreviation^20",
                    "variations^20",
                    "name_normalized^20",
                    "abbreviation_normalized^20",
                    "variations_normalized^20"
                ],
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

    settings = {
        "settings": {
            "analysis": {
                "filter": {
                    "roman_numerals_synonym_filter": {
                        "type": "synonym",
                        "synonyms": [
                            "I, i, 1",
                            "II, ii, 2",
                            "III, iii, 3",
                            "IV, iv, 4",
                            "V, v, 5",
                            "VI, vi, 6",
                            "VII, vii, 7",
                            "VIII, viii, 8",
                        ]
                    }
                },
                "analyzer": {
                    # this should be identical to the one used by default + synonyms
                    # https://www.elastic.co/docs/reference/text-analysis/analysis-standard-analyzer
                    "course_analyzer": {
                        "tokenizer": "standard",
                        "filter": [
                            "lowercase",
                            "roman_numerals_synonym_filter"
                        ]
                    }
                }
            }
        },
        "mappings": {
            "properties": {
                "name": {
                    "type": "text",
                    "analyzer": "course_analyzer"
                },
                "name_normalized": {
                    "type": "text",
                    "analyzer": "course_analyzer"
                },
                "variations": {
                    "type": "text",
                    "analyzer": "course_analyzer"
                },
                "variations_normalized": {
                    "type": "text",
                    "analyzer": "course_analyzer"
                }
            }
        }
    }
    if es.indices.exists(index="courses"):
        es.indices.delete(index="courses")
    es.indices.create(index="courses", body=settings)

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
    # Normalize and split
    norm = normalize_text(search_term)
    numeric_part = "".join(re.findall(r"\d+", norm))
    word_part = "".join(re.findall(r"\D+", norm)).strip()

    should_queries = []

    # 1) If we have a word part, resolve it to subjects first
    if word_part:
        # hit_subjects: e.g. [{"subject_id":"MATH",...}, {"subject_id":"COMPSCI",...}]
        hit_subjects = search_subjects(es, word_part)
        subject_ids = [h["subject_id"] for h in hit_subjects]

        # for each subject match the numeric part
        if numeric_part:
            for subj in subject_ids:
                should_queries.append({
                    "bool": {
                        "must": [
                            # require that the course lists this subject
                            {"term": {"subjects_normalized": normalize_text(subj)}},
                            # and also has the right number
                            {"term": {
                                "course_number": {
                                    "value": int(numeric_part),
                                    "boost": 10.0
                                }
                            }}
                        ]
                    }
                })

    # 2) Always include a fallback on the full text
    should_queries.extend([
        # exact-ish on reference
        {"wildcard": {"course_reference_normalized": f"*{norm}*"}},
        # fuzzy on title
        {
            "multi_match": {
                "query": norm,
                "fields": [
                    "course_title_normalized^5",
                    "course_reference_normalized^4"
                ],
                "fuzziness": "AUTO",
                "analyzer": "course_analyzer"
            }
        }
    ])

    # 3) Wrap it up
    es_query = {
        "query": {
            "bool": {
                "should": should_queries,
                "minimum_should_match": 1
            }
        },
        "size": 10
    }

    resp = es.search(index="courses", body=es_query)
    hits = resp.get("hits", {}).get("hits", [])
    return [
        {
            "course_id": h["_id"],
            "course_title": h["_source"]["course_title"],
            "course_number": h["_source"]["course_number"],
            "subjects": h["_source"]["subjects"],
            "departments": h["_source"]["departments"],
            "score": h["_score"]
        }
        for h in hits
    ]

def load_instructors(es, instructors):
    """
    Index instructors into Elasticsearch.
    Adds normalized versions for all text fields.
    """
    # literally all it does it to remove tokens shorter than 2 characters after analyzer tokenizes the string 
    # done to remove middle name tokens like "I" filling up the results
    settings = {
        "settings": {
            "analysis": {
                "filter": {
                    "min_length_filter": {
                        "type": "length",
                        "min": 2  
                    }
                },
                "analyzer": {
                    "instructor_analyzer": {
                        "type": "custom",
                        "tokenizer": "standard",
                        "filter": [
                            "lowercase",
                            "min_length_filter"
                        ]
                    }
                }
            }
        },
        "mappings": {
            "properties": {
                "name": {
                    "type": "text",
                    "analyzer": "instructor_analyzer",
                    "search_analyzer": "instructor_analyzer"
                },
                "official_name": {
                    "type": "text",
                    "analyzer": "instructor_analyzer",
                    "search_analyzer": "instructor_analyzer"
                },
            }
        }
    }

    # Create index with settings
    if es.indices.exists(index="instructors"):
        es.indices.delete(index="instructors")
    es.indices.create(index="instructors", body=settings)

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
                    # Primary name fields with high boost
                    {
                        "multi_match": {
                            "query": search_term,
                            "fields": [
                                "name^10",
                                "official_name^8",
                                "name_normalized^10",
                                "official_name_normalized^8"
                            ],
                            "type": "best_fields",
                            "fuzziness": "AUTO",
                            "analyzer": "instructor_analyzer",
                            "slop": 1 
                        }
                    },
                    # Department and position with medium boost
                    {
                        "multi_match": {
                            "query": search_term,
                            "fields": [
                                "department^5",
                                "position^5",
                                "department_normalized^5",
                                "position_normalized^5"
                            ],
                            "type": "best_fields",
                            "fuzziness": "AUTO"
                        }
                    },
                    # Email with lower boost
                    {
                        "multi_match": {
                            "query": search_term,
                            "fields": [
                                "email^2",
                                "email_normalized^2"
                            ],
                            "type": "best_fields",
                            "fuzziness": "AUTO"
                        }
                    }
                ],
                    # {
                    #     "query_string": {
                    #         "query": f"*{search_term}*",
                    #         "fields": [
                    #             "name",
                    #             "official_name",
                    #             "email",
                    #             "position",
                    #             "department",
                    #             "name_normalized",
                    #             "official_name_normalized",
                    #             "email_normalized",
                    #             "position_normalized",
                    #             "department_normalized"
                    #         ],
                    #         "analyze_wildcard": True
                    #     }
                    # }
                
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