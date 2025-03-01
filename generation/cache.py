import os
import json

from save import write_file


def write_cache(directory: str, directory_tuple: tuple[str, ...], filename: str, data, logger) -> None:
    """
    Writes data to a JSON cache file by reusing the write_file function.

    Parameters:
        directory (str): Base directory where the cache file will be stored.
        directory_tuple (tuple[str, ...]): Tuple representing subdirectories.
        filename (str): Name of the JSON file (without the .json extension).
        data: Dictionary, list, set, tuple, or JsonSerializable object to be written.
        logger: Logger instance for logging messages.
    """

    write_file(directory, directory_tuple, filename, data, logger)


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

    logger.info(f"Cache read from {file_path}")
    return data
