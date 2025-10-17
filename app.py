# app.py
from fastapi import FastAPI, UploadFile, Form
from fastapi.responses import JSONResponse
import os
import json
import uuid
import numpy as np

from core.utils import save_upload, generate_doc_id
from ingestion.pdf_ingestor import ingest_pdf
from ingestion.docx_ingestor import ingest_docx
from ingestion.txt_ingestor import ingest_txt
from processing.chunking import chunk_text
from processing.embedding import embed_chunks
from processing.vectorstore import build_faiss_index, load_faiss_index, search_index
from llm.gemini_client import ask_gemini

# -------------------------------
# Storage paths
# -------------------------------
DOC_METADATA_FILE = "storage/doc_metadata.json"
CONVERSATION_FILE = "storage/conversations.json"

os.makedirs("storage", exist_ok=True)

# Ensure files exist and are valid JSON
for file_path in [DOC_METADATA_FILE, CONVERSATION_FILE]:
    if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
        with open(file_path, "w") as f:
            json.dump({}, f)

# Now safely load
with open(DOC_METADATA_FILE, "r") as f:
    doc_metadata = json.load(f)

with open(CONVERSATION_FILE, "r") as f:
    conversations = json.load(f)
    
os.makedirs("storage/indexes", exist_ok=True)

# -------------------------------
# Load persistent data
# -------------------------------
doc_metadata = json.load(open(DOC_METADATA_FILE, "r")) if os.path.exists(DOC_METADATA_FILE) else {}
conversations = json.load(open(CONVERSATION_FILE, "r")) if os.path.exists(CONVERSATION_FILE) else {}

# -------------------------------
# FastAPI App
# -------------------------------
app = FastAPI(title="RAG Document Processing API")

# -------------------------------
# /api/embedding
# -------------------------------
@app.post("/api/embedding")
async def embed_document(file: UploadFile):
    try:
        file_path = save_upload(file)
        file_name = file.filename.lower()

        # Detect file type
        if file_name.endswith(".pdf"):
            pages = ingest_pdf(file_path)
        elif file_name.endswith(".docx"):
            pages = ingest_docx(file_path)
        elif file_name.endswith(".txt"):
            pages = ingest_txt(file_path)
        else:
            return JSONResponse(status_code=400, content={"status":"error","message":"Unsupported file type."})

        # Chunk text
        all_chunks, chunks_meta = [], []
        for page in pages:
            page_num, text = page["page"], page["text"]
            for c in chunk_text(text):
                all_chunks.append(c)
                chunks_meta.append({"page": page_num, "chunk": c})

        # Embed
        embeddings = embed_chunks(all_chunks)

        # Build FAISS
        document_id = generate_doc_id()
        build_faiss_index(embeddings, document_id)

        # Save metadata
        doc_metadata[document_id] = {"chunks_meta": chunks_meta, "file_name": file.filename}
        with open(DOC_METADATA_FILE, "w") as f:
            json.dump(doc_metadata, f, indent=2)

        return {"status":"success","message":"Document embedded successfully.","document_id":document_id}

    except Exception as e:
        return JSONResponse(status_code=500, content={"status":"error","message":"Failed to embed document","error_details": str(e)})

# -------------------------------
# /api/query
# -------------------------------
@app.post("/api/query")
async def query_document(query: str = Form(...), document_id: str = Form(...),
                         require_citations: bool = Form(False), conversation_id: str = Form(None)):
    try:
        # Load metadata
        doc_metadata_local = json.load(open(DOC_METADATA_FILE, "r")) if os.path.exists(DOC_METADATA_FILE) else {}
        if document_id not in doc_metadata_local:
            return JSONResponse(status_code=400, content={"status":"error","message":"Invalid document_id."})

        # FAISS search
        index = load_faiss_index(document_id)
        query_emb = embed_chunks([query])[0]
        top_idx = search_index(index, query_emb, top_k=3)
        selected_chunks = [doc_metadata_local[document_id]["chunks_meta"][i]["chunk"] for i in top_idx]
        context = "\n\n".join(selected_chunks)

        # LLM
        answer = ask_gemini(context, query)

        # Citations
        citations = []
        if require_citations:
            for i in top_idx:
                chunk_meta = doc_metadata_local[document_id]["chunks_meta"][i]
                citations.append({"page": chunk_meta["page"], "document_name": doc_metadata_local[document_id]["file_name"]})
        citations = sorted(citations, key=lambda x:x["page"])

        # Conversation
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
            conversations[conversation_id] = []
        conversations[conversation_id].append({"query": query, "answer": answer, "citations": citations})
        with open(CONVERSATION_FILE, "w") as f:
            json.dump(conversations, f, indent=2)

        return {"status":"success","response":{"answer": answer,"citations": citations}, "conversation_id": conversation_id}

    except Exception as e:
        return JSONResponse(status_code=500, content={"status":"error","message":"Failed to process query","error_details": str(e)})
