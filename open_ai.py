import numpy as np


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
