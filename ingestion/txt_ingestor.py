# ingestion/txt_ingestor.py
def ingest_txt(file_path):
    """
    Reads plain text files.
    Returns [{"page": 1, "text": content}]
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()
    return [{"page": 1, "text": text}]
