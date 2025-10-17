# processing/embedding.py
from sentence_transformers import SentenceTransformer
import numpy as np

# Load model once
embed_model = SentenceTransformer('all-MiniLM-L6-v2')

def embed_chunks(chunks):
    """
    Converts a list of text chunks into embeddings.
    Returns a numpy array of shape (num_chunks, embedding_dim)
    """
    if not chunks:
        return np.array([], dtype='float32')
    return embed_model.encode(chunks, convert_to_numpy=True, normalize_embeddings=True)
