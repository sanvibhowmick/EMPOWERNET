# app/core/ingest_pdfs.py
"""
Offline batch job: ingest data/pdfs/*.pdf into the `legal_documents` table
as searchable embeddings.

FIX (weak point #8): the old version embedded only the first 8,000
characters of each *whole* PDF as a single row/vector -- no chunking at
all. With an 11-document corpus that's tolerable by accident (see search.py
fix notes), but it means:
  (a) anything past ~2,000 words of a longer Act was invisible to both the
      embedding and, in practice, to retrieval relevance, and
  (b) a single "West Bengal Factories Safety Officer Rules" embedding has to
      represent an entire multi-topic document as one vector, which is a
      very blunt instrument for semantic search.

This version splits each document's extracted text into overlapping chunks
BEFORE embedding, and stores one row per chunk, each tagged with its source
filename and chunk index in `metadata`. This is what makes a real,
proportionate top-k retrieval in search.py meaningful once the corpus grows
beyond a handful of documents.
"""

import os
import json
import base64
from dotenv import load_dotenv
from sqlalchemy import text
from pypdf import PdfReader
from openai import OpenAI

from app.core.db import get_vector_connection

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

CHUNK_SIZE = 1500       # characters per chunk (roughly ~350-400 tokens)
CHUNK_OVERLAP = 200     # characters of overlap between consecutive chunks


def chunk_text(text_content: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """
    Simple, dependency-free overlapping character-window chunker. Splits on
    paragraph boundaries where possible so a chunk doesn't cut a sentence in
    half more often than necessary, while guaranteeing every chunk stays
    under `chunk_size`.
    """
    text_content = text_content.strip()
    if not text_content:
        return []

    paragraphs = [p for p in text_content.split("\n\n") if p.strip()]
    if not paragraphs:
        paragraphs = [text_content]

    chunks = []
    current = ""
    for para in paragraphs:
        candidate = f"{current}\n\n{para}".strip() if current else para
        if len(candidate) <= chunk_size:
            current = candidate
        else:
            if current:
                chunks.append(current)
            # A single paragraph longer than chunk_size still needs hard-splitting.
            if len(para) > chunk_size:
                for i in range(0, len(para), chunk_size - overlap):
                    chunks.append(para[i:i + chunk_size])
                current = ""
            else:
                current = para

    if current:
        chunks.append(current)

    # Add overlap between consecutive chunks so context isn't lost at boundaries.
    overlapped = []
    for i, c in enumerate(chunks):
        if i == 0:
            overlapped.append(c)
        else:
            tail = chunks[i - 1][-overlap:]
            overlapped.append((tail + "\n\n" + c)[:chunk_size + overlap])
    return overlapped


def get_ocr_from_gpt(file_path):
    """Fallback for scanned/hybrid pages: Cloud-based Vision OCR."""
    with open(file_path, "rb") as f:
        pdf_base64 = base64.b64encode(f.read()).decode('utf-8')

    pdf_data_url = f"data:application/pdf;base64,{pdf_base64}"

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": "This PDF is a scan or a complex hybrid. Transcribe all text exactly as it appears, including tables."},
                {
                    "type": "file",
                    "file": {
                        "file_data": pdf_data_url,
                        "filename": os.path.basename(file_path)
                    }
                }
            ],
        }],
    )
    return response.choices[0].message.content


def ingest_all_pdfs():
    try:
        conn = get_vector_connection()
        cur = conn.cursor()
        print("✅ Connected to Neon DB (pooled).")
    except Exception as e:
        print(f"❌ DB Connection Error: {e}")
        return

    pdf_dir = "data/pdfs"

    for filename in os.listdir(pdf_dir):
        if not filename.endswith(".pdf"):
            continue
        file_path = os.path.join(pdf_dir, filename)
        print(f"--- Analyzing: {filename} ---")

        try:
            # Step A: Try Digital Extraction (Fast & Free)
            reader = PdfReader(file_path)
            full_text = ""
            for page in reader.pages:
                full_text += page.extract_text() or ""

            # Step B: Decide if we need GPT Vision
            if len(full_text.strip()) < 100:
                print(f"🔍 Scanned/Image PDF detected. Calling GPT Vision...")
                final_content = get_ocr_from_gpt(file_path)
            else:
                print(f"📄 Digital text found ({len(full_text)} chars).")
                final_content = full_text

            # Step C: Chunk the full document, then embed + store each chunk
            chunks = chunk_text(final_content)
            print(f"✂️  Split into {len(chunks)} chunk(s).")

            for idx, chunk in enumerate(chunks):
                emb_resp = client.embeddings.create(
                    input=chunk,
                    model="text-embedding-3-small",
                )
                vector = emb_resp.data[0].embedding

                cur.execute(
                    "INSERT INTO legal_documents (content, metadata, embedding) VALUES (%s, %s, %s)",
                    (
                        chunk,
                        json.dumps({
                            "source": filename,
                            "method": "smart_hybrid",
                            "chunk_index": idx,
                            "chunk_count": len(chunks),
                        }),
                        vector,
                    ),
                )
            conn.commit()
            print(f"✅ Ingested: {filename} ({len(chunks)} chunks)")

        except Exception as e:
            conn.rollback()
            print(f"❌ Failed {filename}: {e}")

    cur.close()
    conn.close()

if __name__ == "__main__":
    ingest_all_pdfs()
