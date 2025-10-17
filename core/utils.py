# core/utils.py
import uuid
import os

def generate_doc_id():
    """
    Returns a unique document ID.
    """
    return str(uuid.uuid4())

def save_upload(file):
    """
    Saves uploaded file to 'uploads/' and returns the path.
    """
    os.makedirs("uploads", exist_ok=True)
    file_path = f"uploads/{file.filename}"
    with open(file_path, "wb") as f:
        f.write(file.file.read())
    return file_path
