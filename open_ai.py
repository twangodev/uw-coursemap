from logging import Logger

import numpy as np
from openai import OpenAI

def get_openai_client(api_key: str, logger: Logger, show_api_key: bool):
    """
    Returns an OpenAI client object.
    """
    if api_key is None or api_key == "REPLACE_WITH_OPENAI_API_KEY":
        logger.warning("No OpenAI API key provided.")
        return None
    logger.debug("Creating OpenAI client" + (f" with API key {api_key}" if show_api_key else ""))
    return OpenAI(api_key=api_key)

def get_embedding(client, text, model="text-embedding-3-small"):
    """
    Generates an embedding for the given text using OpenAI's embeddings API.
    """
    response = client.embeddings.create(input=text, model=model)
    return response.data[0].embedding

def cosine_similarity(vec_a, vec_b):
    """
    Computes the cosine similarity between two vectors.
    """
    return np.dot(vec_a, vec_b) / (np.linalg.norm(vec_a) * np.linalg.norm(vec_b))
