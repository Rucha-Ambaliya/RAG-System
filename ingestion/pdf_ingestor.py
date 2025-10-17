# ingestion/pdf_ingestor.py
import pdfplumber
from pdf2image import convert_from_path
import pytesseract

def ingest_pdf(file_path):
    """
    Extracts text from PDF pages.
    Uses OCR if page has no extractable text.
    Returns a list of dicts: [{"page": int, "text": str}]
    """
    results = []
    with pdfplumber.open(file_path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            if not text or text.strip() == "":
                img = convert_from_path(file_path, first_page=i+1, last_page=i+1)[0]
                text = pytesseract.image_to_string(img)
            results.append({"page": i+1, "text": text})
    return results
