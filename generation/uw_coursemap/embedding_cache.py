import os
import tempfile
from logging import getLogger

import numpy as np

from uw_coursemap.save import format_file_size

logger = getLogger(__name__)


def write_embedding(
    directory: str, directory_tuple: tuple[str, ...], filename: str, embedding
):
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
    # Readers must never observe an incompletely written array.
    with tempfile.NamedTemporaryFile(
        dir=directory_path, suffix=".npy", delete=False
    ) as stream:
        temporary = stream.name
        try:
            np.save(stream, embedding)
            stream.flush()
            os.replace(temporary, file_path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

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
    for attr in [
        "model_name",
        "_model_name",
        "model_name_or_path",
        "_model_name_or_path",
    ]:
        if hasattr(model, attr):
            value = getattr(model, attr)
            if value and isinstance(value, str):
                model_name = value
                break

    # If still no model name found, try to get it from the model card or config
    if not model_name and hasattr(model, "_modules") and hasattr(model._modules, "get"):
        # Try to extract from the first transformer module
        transformer_module = model._modules.get("0")
        if transformer_module and hasattr(transformer_module, "auto_model"):
            auto_model = transformer_module.auto_model
            if hasattr(auto_model, "name_or_path"):
                model_name = auto_model.name_or_path

    # Final fallback
    if not model_name:
        model_name = "unknown_model"

    revision = getattr(model, "pipeline_revision", None)
    if revision:
        model_name = f"{model_name}@{revision}"

    # Sanitize the model name for use in file paths
    sanitized_name = (
        model_name.replace("/", "_")
        .replace("\\", "_")
        .replace(":", "_")
        .replace(" ", "_")
    )
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
