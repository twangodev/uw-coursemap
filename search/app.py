import logging
import random
from argparse import ArgumentParser
from os import environ

import coloredlogs
from elasticsearch import Elasticsearch
from flask import Flask, request, jsonify
from flask_cors import CORS

from data import get_instructors, get_courses, get_subjects, normalize_text
from es_util import load_courses, search_courses, load_instructors, search_instructors, load_subjects, search_subjects

ES_HOST = environ.get("ES_HOST")
ES_USERNAME = environ.get("ES_USERNAME")
ES_PASSWORD = environ.get("ES_PASSWORD")
ES_VERIFY_CERTS = environ.get("ES_VERIFY_CERTS")

if not ES_HOST:
    raise EnvironmentError("ES_HOST environment variable not set")
if not ES_USERNAME:
    raise EnvironmentError("ES_USERNAME environment variable not set")
if not ES_PASSWORD:
    raise EnvironmentError("ES_PASSWORD environment variable not set")
if ES_VERIFY_CERTS is None:
    raise EnvironmentError("ES_VERIFY_CERTS environment variable not set")

verify_certs = ES_VERIFY_CERTS.lower() in ("true", "1", "yes")

es = Elasticsearch(
    ES_HOST,
    basic_auth=(ES_USERNAME, ES_PASSWORD),
    verify_certs=verify_certs
)

app = Flask(__name__)
cors = CORS(app)

data_dir_default = environ.get("DATA_DIR", "../generation/data")

def generate_parser():
    """
    Build the argument parser for command line arguments.
    """
    arg_parser = ArgumentParser(
        description="Search for courses"
    )
    arg_parser.add_argument(
        "data_dir",
        type=str,
        nargs="?",
        default=data_dir_default,
        help="Directory to pull generated data."
    )
    arg_parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging (DEBUG level). This will also enable Flask debug mode, and should not be used in production.",
    )
    return arg_parser

@app.route('/search', methods=['POST'])
def search():
    # Expecting a JSON body like { "query": "Python" }
    data = request.get_json()
    search_term = data.get("query")

    normalized_search_term = normalize_text(search_term)

    return {
        "courses": search_courses(es, normalized_search_term),
        "instructors": search_instructors(es, normalized_search_term),
        "subjects": search_subjects(es, normalized_search_term),
    }

@app.route('/random-courses', methods=['GET'])
def get_random_courses():
    """Returns 5 random courses from the dataset."""
    if not courses:
        return jsonify({"error": "No courses available"}), 404

    # Ensure we don't try to sample more courses than exist
    num_courses = min(5, len(courses))

    # Select 5 unique random course IDs
    random_course_ids = random.sample(list(courses.keys()), num_courses)

    # Retrieve the full course details
    random_courses = [{"id": course_id, **courses[course_id]} for course_id in random_course_ids]

    return jsonify(random_courses)


def clear_elasticsearch():

    indexes = ["courses", "instructors", "subjects"]

    for index in indexes:
        if es.indices.exists(index=index):
            es.indices.delete(index=index)

parser = generate_parser()
args = parser.parse_args()

data_dir = str(args.data_dir)
verbose = bool(args.verbose)

logger = logging.getLogger(__name__)
logging_level = logging.DEBUG if verbose else logging.INFO
coloredlogs.install(level=logging_level, logger=logger)

subjects = get_subjects(data_dir, logger)
instructors = get_instructors(data_dir, logger)
courses = get_courses(data_dir, subjects, logger)

clear_elasticsearch()

load_subjects(es, subjects)
load_courses(es, courses)
load_instructors(es, instructors)

if __name__ == "__main__":
    app.run(debug=verbose)
