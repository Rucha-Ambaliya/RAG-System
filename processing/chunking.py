# processing/chunking.py
def chunk_text(text, chunk_size=500, overlap=50):
    """
    Splits text into chunks of specified size with optional overlap.
    Returns a list of string chunks.
    """
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i+chunk_size])
        chunks.append(chunk)
    return chunks
