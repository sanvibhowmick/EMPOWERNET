import os
import json
import base64
import psycopg2
from dotenv import load_dotenv
from pgvector.psycopg2 import register_vector
from pypdf import PdfReader
from openai import OpenAI

# 1. Setup
load_dotenv()
DB_URL = os.getenv("DATABASE_URL")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_ocr_from_gpt(file_path):
    """Fallback for scanned/hybrid pages: Cloud-based Vision OCR."""
    with open(file_path, "rb") as f:
        # Step 1: Encode to base64
        pdf_base64 = base64.b64encode(f.read()).decode('utf-8')
    
    # Step 2: ADD THE REQUIRED PREFIX (This fixes your 400 error)
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
                        "file_data": pdf_data_url, # Now includes the data prefix
                        "filename": os.path.basename(file_path)
                    }
                }
            ],
        }],
    )
    return response.choices[0].message.content

def ingest_all_pdfs():
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        register_vector(conn)
        print("✅ Connected to Neon DB.")
    except Exception as e:
        print(f"❌ DB Connection Error: {e}")
        return

    pdf_dir = "data/pdfs"
    
    for filename in os.listdir(pdf_dir):
        if not filename.endswith(".pdf"): continue
        file_path = os.path.join(pdf_dir, filename)
        print(f"--- Analyzing: {filename} ---")
        
        try:
            # Step A: Try Digital Extraction (Fast & Free)
            reader = PdfReader(file_path)
            full_text = ""
            for page in reader.pages:
                full_text += page.extract_text() or ""

            # Step B: Decide if we need GPT Vision
            # If local text is too short, we assume it's an image or scan.
            if len(full_text.strip()) < 100:
                print(f"🔍 Scanned/Image PDF detected. Calling GPT Vision...")
                final_content = get_ocr_from_gpt(file_path)
            else:
                print(f"📄 Digital text found ({len(full_text)} chars).")
                final_content = full_text

            # Step C: Create Embedding (max 8000 chars for safety)
            emb_resp = client.embeddings.create(
                input=final_content[:8000], 
                model="text-embedding-3-small"
            )
            vector = emb_resp.data[0].embedding
            
            # Step D: Save to Neon
            cur.execute(
                "INSERT INTO legal_documents (content, metadata, embedding) VALUES (%s, %s, %s)",
                (final_content, json.dumps({"source": filename, "method": "smart_hybrid"}), vector)
            )
            conn.commit()
            print(f"✅ Ingested: {filename}")

        except Exception as e:
            conn.rollback()
            print(f"❌ Failed {filename}: {e}")

    cur.close()
    conn.close()

if __name__ == "__main__":
    ingest_all_pdfs()