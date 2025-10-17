# processing/vectorstore.py
import faiss
import numpy as np
import os

def build_faiss_index(embeddings, document_id):
    """
    Builds and saves a FAISS index for a given document's embeddings.
    """
    embeddings = np.array(embeddings).astype('float32')
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)
    os.makedirs("storage/indexes", exist_ok=True)
    faiss.write_index(index, f"storage/indexes/{document_id}.index")

def load_faiss_index(document_id):
    """
    Loads FAISS index from disk for a given document.
    """
    path = f"storage/indexes/{document_id}.index"
    if not os.path.exists(path):
        raise FileNotFoundError(f"Index for document {document_id} not found.")
    return faiss.read_index(path)

def search_index(index, query_emb, top_k=3):
    """
    Returns top_k indices from FAISS search for a given query embedding.
    """
    query_emb = np.array([query_emb]).astype('float32')
    D, I = index.search(query_emb, top_k)
    return I[0]
