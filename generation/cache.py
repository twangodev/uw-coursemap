import os
import json

from course import Course
from save import write_file, list_files


def read_cache(directory: str, directory_tuple: tuple[str, ...], filename: str, logger):
    """
    Reads data from a JSON cache file.
    
    Parameters:
        directory (str): Base directory where the cache file is stored.
        directory_tuple (tuple[str, ...]): Tuple representing subdirectories.
        filename (str): Name of the JSON file (without the .json extension).
        logger: Logger instance for logging messages.
    
    Returns:
        The data read from the JSON file, or None if the file does not exist.
    """
    # Create the full directory path
    directory_path = os.path.join(directory, *directory_tuple)

    # Sanitize the filename to remove problematic characters
    sanitized_filename = filename.replace("/", "_").replace(" ", "_")

    # Full path to the JSON file
    file_path = os.path.join(directory_path, f"{sanitized_filename}.json")

    if not os.path.exists(file_path):
        logger.warning(f"Cache file {file_path} does not exist.")
        return None

    with open(file_path, 'r', encoding='utf-8') as json_file:
        data = json.load(json_file)

    logger.debug(f"Cache read from {file_path}")
    return data

def write_subject_to_full_subject_cache(cache_dir, subject_to_full_subject, logger):
    write_file(cache_dir, (), "subjects", subject_to_full_subject, logger)

def write_course_ref_to_course_cache(cache_dir, course_ref_to_course, logger):
    write_file(cache_dir, (), "courses", course_ref_to_course, logger)

def write_terms_cache(cache_dir, terms, logger):
    write_file(cache_dir, (), "terms", terms, logger)

def write_instructors_to_rating_cache(cache_dir, instructor_to_rating, logger):
    write_file(cache_dir, (), "instructors", instructor_to_rating, logger)


def read_course_ref_to_course_cache(cache_dir, logger):
    str_course_ref_to_course = read_cache(cache_dir, (), "courses", logger)
    return { Course.Reference.from_string(key): Course.from_json(value) for key, value in str_course_ref_to_course.items() }

def read_terms_cache(cache_dir, logger):
    str_terms = read_cache(cache_dir, (), "terms", logger)
    return { int(term_code): term_name for term_code, term_name in str_terms.items() }