from docx import Document
from PIL import Image
import pytesseract
import io
from processing.chunking import chunk_text

def ingest_docx(file_path, chunk_size=500, overlap=50):
    """
    Extracts text from DOCX paragraphs and inline images.
    Splits text into chunks and assigns proper page numbers.

    Returns:
        List of dicts: [{"page": int, "text": str}]
    """
    doc = Document(file_path)
    text_blocks = []
    page_counter = 1

    # Process paragraphs
    temp_text = ""
    for p in doc.paragraphs:
        line = p.text.strip()
        if not line:
            continue
        temp_text += line + " "
        # If accumulated text exceeds chunk_size, create a block
        if len(temp_text.split()) >= chunk_size:
            chunks = chunk_text(temp_text, chunk_size=chunk_size, overlap=overlap)
            for chunk in chunks:
                text_blocks.append({"page": page_counter, "text": chunk})
                page_counter += 1
            temp_text = ""

    # Add remaining text
    if temp_text.strip():
        chunks = chunk_text(temp_text, chunk_size=chunk_size, overlap=overlap)
        for chunk in chunks:
            text_blocks.append({"page": page_counter, "text": chunk})
            page_counter += 1

    # OCR for inline shapes (images)
    for shape in doc.inline_shapes:
        try:
            if shape.type == 3:  # InlineShapeType.PICTURE
                img_stream = io.BytesIO(shape._inline.graphic.graphicData.pic.blipFill.blip._blob)
                img = Image.open(img_stream)
                text = pytesseract.image_to_string(img)
                if text.strip():
                    chunks = chunk_text(text, chunk_size=chunk_size, overlap=overlap)
                    for chunk in chunks:
                        text_blocks.append({"page": page_counter, "text": chunk})
                        page_counter += 1
        except Exception as e:
            print(f"OCR failed for an image: {e}")
            continue

    return text_blocks
