import logging
from argparse import ArgumentParser
import coloredlogs
from elasticsearch import Elasticsearch
from flask import Flask, request
from flask_cors import CORS

from data import get_instructors, get_courses, get_subjects, normalize_text
from es_util import load_courses, search_courses, load_instructors, search_instructors, load_subjects, search_subjects

app = Flask(__name__)
cors = CORS(app)
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
        help="Enable verbose logging (DEBUG level). This will also enable Flask debug mode, and should not be used in production.",
    )
    return parser

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

def clear_elasticsearch():

    indexes = ["courses", "instructors", "subjects"]

    for index in indexes:
        if es.indices.exists(index=index):
            es.indices.delete(index=index)

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

    clear_elasticsearch()

    load_subjects(es, subjects)
    load_courses(es, courses)
    load_instructors(es, instructors)

    app.run(debug=verbose)
