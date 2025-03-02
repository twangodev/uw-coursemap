from elasticsearch import helpers


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