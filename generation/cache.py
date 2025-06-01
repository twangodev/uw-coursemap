import json
import os
from logging import Logger

import numpy as np

from course import Course
from instructors import FullInstructor
from save import write_file, format_file_size

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


def write_graphs_cache(cache_dir, global_graph, subject_to_graph, course_to_graph, global_style, subject_to_style, color_map, logger):
    write_file(cache_dir, ("graphs",), "global_graph", global_graph, logger)
    write_file(cache_dir, ("graphs",), "subject_to_graph", subject_to_graph, logger)
    write_file(cache_dir, ("graphs",), "course_to_graph", course_to_graph, logger)

    write_file(cache_dir, ("graphs",), "global_style", global_style, logger)
    write_file(cache_dir, ("graphs",), "subject_to_style", subject_to_style, logger)

    write_file(cache_dir, ("graphs",), "color_map", color_map, logger)

def read_course_ref_to_course_cache(cache_dir, logger):
    str_course_ref_to_course = read_cache(cache_dir, (), "courses", logger)
    return {Course.Reference.from_string(key): Course.from_json(value) for key, value in
            str_course_ref_to_course.items()}


def read_terms_cache(cache_dir, logger):
    str_terms = read_cache(cache_dir, (), "terms", logger)
    if str_terms is None:
        return {}
    return {int(term_code): term_name for term_code, term_name in str_terms.items()}


def read_subject_to_full_subject_cache(cache_dir, logger):
    return read_cache(cache_dir, (), "subjects", logger)


def read_graphs_cache(cache_dir, logger):
    global_graph = read_cache(cache_dir, ("graphs",), "global_graph", logger)
    subject_to_graph = read_cache(cache_dir, ("graphs",), "subject_to_graph", logger)
    course_to_graph = read_cache(cache_dir, ("graphs",), "course_to_graph", logger)
    global_style = read_cache(cache_dir, ("graphs",), "global_style", logger)
    subject_to_style = read_cache(cache_dir, ("graphs",), "subject_to_style", logger)

    return global_graph, subject_to_graph, course_to_graph, global_style, subject_to_style


def read_instructors_to_rating_cache(cache_dir, logger):
    instructors_to_rating = read_cache(cache_dir, (), "instructors", logger)
    if instructors_to_rating is None:
        return {}
    return {name: FullInstructor.from_json(full_instructor) for name, full_instructor in instructors_to_rating.items()}

def read_quick_statistics_cache(cache_dir, logger):
    quick_statistics = read_cache(cache_dir, (), "quick_statistics", logger)
    if quick_statistics is None:
        return {}
    return quick_statistics

def write_quick_statistics_cache(cache_dir, quick_statistics, logger):
    write_file(cache_dir, (), "quick_statistics", quick_statistics, logger)

def read_explorer_extras_cache(cache_dir, logger):
    explorer_extras = read_cache(cache_dir, ("extras",), "explorer_extras", logger)
    if explorer_extras is None:
        return {}
    return explorer_extras

def write_explorer_extras_cache(cache_dir, explorer_extras, logger):
    write_file(cache_dir, ("extras",), "explorer_extras", explorer_extras, logger)

def write_embedding(directory: str, directory_tuple: tuple[str, ...], filename: str, embedding, logger: Logger):
    """
    Writes a numpy array (embedding) to an .npy file.

    Parameters:
        directory (str): Base directory.
        directory_tuple (tuple[str, ...]): Tuple representing subdirectories.
        filename (str): Name of the file (without the .npy extension).
        embedding (np.ndarray): The embedding data to be saved.
        logger (Logger): Logger instance for logging messages.
    """
    # Create the full directory path.
    directory_path = os.path.join(directory, *directory_tuple)
    os.makedirs(directory_path, exist_ok=True)

    # Sanitize the filename to remove problematic characters.
    sanitized_filename = filename.replace("/", "_").replace(" ", "_")
    file_path = os.path.join(directory_path, f"{sanitized_filename}.npy")

    # Save the embedding using numpy's binary format.
    np.save(file_path, embedding)

    # Calculate file size and log it.
    file_size = os.path.getsize(file_path)
    readable_size = format_file_size(file_size)
    logger.debug(f"Embedding saved to {file_path} ({readable_size})")


def read_embedding(directory: str, directory_tuple: tuple[str, ...], filename: str, logger: Logger):
    """
    Reads a numpy array (embedding) from an .npy file.

    Parameters:
        directory (str): Base directory where the embedding file is stored.
        directory_tuple (tuple[str, ...]): Tuple representing subdirectories.
        filename (str): Name of the file (without the .npy extension).
        logger (Logger): Logger instance for logging messages.

    Returns:
        The loaded numpy array, or None if the file does not exist.
    """
    # Create the full directory path.
    directory_path = os.path.join(directory, *directory_tuple)

    # Sanitize the filename.
    sanitized_filename = filename.replace("/", "_").replace(" ", "_")
    file_path = os.path.join(directory_path, f"{sanitized_filename}.npy")

    # Check if the file exists.
    if not os.path.exists(file_path):
        logger.debug(f"Embedding file {file_path} does not exist.")
        return None

    try:
        embedding = np.load(file_path)
        logger.debug(f"Embedding read from {file_path}")
        return embedding
    except Exception as e:
        logger.warning(f"Failed to load embedding from {file_path}: {e}")
        return None


def read_embedding_cache(cache_dir, sha256hash: str, logger: Logger):
    return read_embedding(cache_dir, ("embeddings",), sha256hash, logger)


def write_embedding_cache(cache_dir, sha256hash: str, embedding, logger: Logger):
    write_embedding(cache_dir, ("embeddings",), sha256hash, embedding, logger)
