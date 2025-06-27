import json
import os
from logging import getLogger

import numpy as np

from course import Course
from enrollment_data import EnrollmentData
from instructors import FullInstructor
from save import write_file, format_file_size

logger = getLogger(__name__)

def read_cache(directory: str, directory_tuple: tuple[str, ...], filename: str):
    """
    Reads data from a JSON cache file.
    
    Parameters:
        directory (str): Base directory where the cache file is stored.
        directory_tuple (tuple[str, ...]): Tuple representing subdirectories.
        filename (str): Name of the JSON file (without the .json extension).

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


def write_subject_to_full_subject_cache(cache_dir, subject_to_full_subject):
    write_file(cache_dir, (), "subjects", subject_to_full_subject)


def write_course_ref_to_course_cache(cache_dir, course_ref_to_course):
    write_file(cache_dir, (), "courses", course_ref_to_course)


def write_terms_cache(cache_dir, terms):
    write_file(cache_dir, (), "terms", terms)


def write_instructors_to_rating_cache(cache_dir, instructor_to_rating):
    write_file(cache_dir, (), "instructors", instructor_to_rating)


def write_graphs_cache(cache_dir, global_graph, subject_to_graph, course_to_graph, global_style, subject_to_style, color_map):
    write_file(cache_dir, ("graphs",), "global_graph", global_graph)
    write_file(cache_dir, ("graphs",), "subject_to_graph", subject_to_graph)
    write_file(cache_dir, ("graphs",), "course_to_graph", course_to_graph)

    write_file(cache_dir, ("graphs",), "global_style", global_style)
    write_file(cache_dir, ("graphs",), "subject_to_style", subject_to_style)

    write_file(cache_dir, ("graphs",), "color_map", color_map)

def read_course_ref_to_course_cache(cache_dir):
    str_course_ref_to_course = read_cache(cache_dir, (), "courses")
    return {Course.Reference.from_string(key): Course.from_json(value) for key, value in
            str_course_ref_to_course.items()}


def read_terms_cache(cache_dir):
    str_terms = read_cache(cache_dir, (), "terms")
    if str_terms is None:
        return {}
    return {int(term_code): term_name for term_code, term_name in str_terms.items()}


def read_subject_to_full_subject_cache(cache_dir):
    return read_cache(cache_dir, (), "subjects")

def read_graphs_cache(cache_dir):
    global_graph = read_cache(cache_dir, ("graphs",), "global_graph")
    subject_to_graph = read_cache(cache_dir, ("graphs",), "subject_to_graph")
    course_to_graph = read_cache(cache_dir, ("graphs",), "course_to_graph")
    global_style = read_cache(cache_dir, ("graphs",), "global_style")
    subject_to_style = read_cache(cache_dir, ("graphs",), "subject_to_style")

    return global_graph, subject_to_graph, course_to_graph, global_style, subject_to_style

def read_instructors_to_rating_cache(cache_dir):
    instructors_to_rating = read_cache(cache_dir, (), "instructors")
    if instructors_to_rating is None:
        return {}
    return {name: FullInstructor.from_json(full_instructor) for name, full_instructor in instructors_to_rating.items()}

def read_quick_statistics_cache(cache_dir):
    quick_statistics = read_cache(cache_dir, (), "quick_statistics")
    if quick_statistics is None:
        return {}
    return quick_statistics

def write_quick_statistics_cache(cache_dir, quick_statistics):
    write_file(cache_dir, (), "quick_statistics", quick_statistics)

def read_explorer_stats_cache(cache_dir):
    explorer_extras = read_cache(cache_dir, (), "explorer_stats")
    if explorer_extras is None:
        return {}
    return explorer_extras

def write_explorer_stats_cache(cache_dir, explorer_extras):
    write_file(cache_dir, (), "explorer_stats", explorer_extras)

def write_embedding(directory: str, directory_tuple: tuple[str, ...], filename: str, embedding):
    """
    Writes a numpy array (embedding) to an .npy file.

    Parameters:
        directory (str): Base directory.
        directory_tuple (tuple[str, ...]): Tuple representing subdirectories.
        filename (str): Name of the file (without the .npy extension).
        embedding (np.ndarray): The embedding data to be saved.
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


def read_embedding(directory: str, directory_tuple: tuple[str, ...], filename: str):
    """
    Reads a numpy array (embedding) from an .npy file.

    Parameters:
        directory (str): Base directory where the embedding file is stored.
        directory_tuple (tuple[str, ...]): Tuple representing subdirectories.
        filename (str): Name of the file (without the .npy extension).

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


def get_model_name_for_cache(model):
    """
    Extract a safe model name for caching purposes.
    
    Args:
        model: SentenceTransformer model instance
        
    Returns:
        str: A sanitized model name suitable for directory names
    """
    # Try various ways to get the model name from SentenceTransformer
    model_name = None
    
    # Check common attributes where model name might be stored
    for attr in ['model_name', '_model_name', 'model_name_or_path', '_model_name_or_path']:
        if hasattr(model, attr):
            value = getattr(model, attr)
            if value and isinstance(value, str):
                model_name = value
                break
    
    # If still no model name found, try to get it from the model card or config
    if not model_name and hasattr(model, '_modules') and hasattr(model._modules, 'get'):
        # Try to extract from the first transformer module
        transformer_module = model._modules.get('0')
        if transformer_module and hasattr(transformer_module, 'auto_model'):
            auto_model = transformer_module.auto_model
            if hasattr(auto_model, 'name_or_path'):
                model_name = auto_model.name_or_path
    
    # Final fallback
    if not model_name:
        model_name = "unknown_model"
    
    # Sanitize the model name for use in file paths
    sanitized_name = model_name.replace("/", "_").replace("\\", "_").replace(":", "_").replace(" ", "_")
    return sanitized_name

def read_embedding_cache(cache_dir, sha256hash: str, model):
    """
    Read cached embedding from model-specific subdirectory.
    
    Args:
        cache_dir: Cache directory
        sha256hash: Hash of the text
        model: Model instance for per-model caching
        
    Returns:
        Cached embedding or None
    """
    model_name = get_model_name_for_cache(model)
    directory_tuple = ("embeddings", model_name)
    return read_embedding(cache_dir, directory_tuple, sha256hash)

def write_embedding_cache(cache_dir, sha256hash: str, embedding, model):
    """
    Write embedding to cache in model-specific subdirectory.
    
    Args:
        cache_dir: Cache directory
        sha256hash: Hash of the text
        embedding: Embedding to cache
        model: Model instance for per-model caching
    """
    model_name = get_model_name_for_cache(model)
    directory_tuple = ("embeddings", model_name)
    write_embedding(cache_dir, directory_tuple, sha256hash, embedding)

def write_new_terms_cache(cache_dir, new_terms):
    """
    Writes new terms to the cache.

    Parameters:
        cache_dir (str): Directory where the cache is stored.
        new_terms (dict): Dictionary of new terms to be cached.
    """
    write_file(cache_dir, (), "new_terms", new_terms)

def read_new_terms_cache(cache_dir):
    new_terms = read_cache(cache_dir, (), "new_terms")
    if new_terms is None:
        return {}

    return {int(term_code): tuple(term_info) for term_code, term_info in new_terms.items()}

def write_course_ref_to_meetings_cache(cache_dir, course_to_meetings):
    """
    Writes course meetings data to the cache.

    Parameters:
        cache_dir (str): Directory where the cache is stored.
        course_to_meetings (dict): Dictionary mapping course identifiers to meeting lists.
    """
    write_file(cache_dir, (), "course_to_meetings", course_to_meetings)

def read_course_ref_to_meetings_cache(cache_dir):
    """
    Reads course meetings data from the cache.

    Parameters:
        cache_dir (str): Directory where the cache is stored.

    Returns:
        dict: Dictionary mapping course identifiers to meeting lists, or empty dict if not found.
    """
    course_to_meetings = read_cache(cache_dir, (), "course_to_meetings")
    if course_to_meetings is None:
        return {}
    return {
        Course.Reference.from_string(key): [EnrollmentData.Meeting.from_json(meeting) for meeting in value]
        for key, value in course_to_meetings.items()
    }

