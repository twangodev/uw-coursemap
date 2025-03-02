import logging
from argparse import ArgumentParser

import coloredlogs
from elasticsearch import Elasticsearch
from flask import Flask, request

from data import get_instructors, get_courses, get_subjects
from es_util import load_courses, search_courses, load_instructors, search_instructors

app = Flask(__name__)
es = Elasticsearch(
    "https://localhost:9200",
    basic_auth=("elastic", "changeme"),
    verify_certs=False
)

def generate_parser():
    """
    Build the argument parser for command line arguments.
    """
    parser = ArgumentParser(
        description="Search for courses"
    )
    parser.add_argument(
        "data_dir",
        type=str,
        help="Directory to pull generated data.",
        default="../generation/data"
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging (DEBUG level)",
    )
    return parser

@app.route('/search', methods=['POST'])
def search():
    # Expecting a JSON body like { "query": "Python" }
    data = request.get_json()
    search_term = data.get("query")

    return {
        "courses": search_courses(es, search_term),
        "instructors": search_instructors(es, search_term)
    }

def clear_elasticsearch():
    index_name = "courses"
    if es.indices.exists(index=index_name):
        es.indices.delete(index=index_name)
        print(f"Deleted existing index '{index_name}'")

if __name__ == "__main__":

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

    load_courses(es, courses)
    load_instructors(es, instructors)

    app.run(debug=True)
