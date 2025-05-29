import logging
import random
from argparse import ArgumentParser
from os import environ

import coloredlogs
from dotenv import load_dotenv
from elasticsearch import Elasticsearch
from flask import Flask, request, jsonify
from flask_cors import CORS

from data import get_instructors, get_courses, get_subjects, normalize_text
from es_util import load_courses, search_courses, load_instructors, search_instructors, load_subjects, search_subjects
from data import get_random_courses as get_random_courses_data

load_dotenv()

ELASTIC_HOST = environ.get("ELASTIC_HOST")
ELASTIC_USERNAME = environ.get("ELASTIC_USERNAME")
ELASTIC_PASSWORD = environ.get("ELASTIC_PASSWORD")
ELASTIC_VERIFY_CERTS = environ.get("ELASTIC_VERIFY_CERTS")

if not ELASTIC_HOST:
    raise EnvironmentError("ELASTIC_HOST environment variable not set")
if not ELASTIC_USERNAME:
    raise EnvironmentError("ELASTIC_USERNAME environment variable not set")
if not ELASTIC_PASSWORD:
    raise EnvironmentError("ELASTIC_PASSWORD environment variable not set")
if ELASTIC_VERIFY_CERTS is None:
    raise EnvironmentError("ELASTIC_VERIFY_CERTS environment variable not set")

verify_certs = ELASTIC_VERIFY_CERTS.lower() in ("true", "1", "yes")

es = Elasticsearch(
    ELASTIC_HOST,
    basic_auth=(ELASTIC_USERNAME, ELASTIC_PASSWORD),
    verify_certs=verify_certs
)

app = Flask(__name__)
cors = CORS(app)

data_dir_default = environ.get("DATA_DIR", "./data")

args = None
verbose = False

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

if __name__ == "__main__":
    parser = generate_parser()
    args = parser.parse_args()

    verbose = bool(args.verbose) if args else verbose


data_dir = args.data_dir if args else data_dir_default

@app.route('/search', methods=['POST'])
def search():
    # Expecting a JSON body like { "query": "Python" }
    data = request.get_json()
    search_term = data.get("query")

    return {
        "courses": search_courses(es, search_term),
        "instructors": search_instructors(es, search_term),
        "subjects": search_subjects(es, search_term),
    }

@app.route('/random-courses', methods=['GET'])
def get_random_courses():
    """Returns 5 random courses from the dataset."""
    random_courses_data = get_random_courses_data(data_dir, subjects, logger, num_courses=5)
    # Retrieve the full course details
    random_courses = [
        {
        "course_id": course_id,
        **courses[course_id]
        } for course_id in random_courses_data 
    ]
    return jsonify(random_courses)

def clear_elasticsearch():

    indexes = ["courses", "instructors", "subjects"]

    for index in indexes:
        if es.indices.exists(index=index):
            es.indices.delete(index=index)

logger = logging.getLogger(__name__)
logging_level = logging.DEBUG if verbose else logging.INFO
coloredlogs.install(level=logging_level, logger=logger)

subjects = get_subjects(data_dir, logger)
courses = get_courses(data_dir, subjects, logger)

if environ.get('WERKZEUG_RUN_MAIN') != 'true':
    # This check prevents the code from running twice when using Flask's reloader
    instructors = get_instructors(data_dir, logger)
    clear_elasticsearch()

    load_subjects(es, subjects)
    load_courses(es, courses)
    load_instructors(es, instructors)

if __name__ == "__main__":
    app.run(debug=verbose)
