# app/core/search.py

import os
import logging
from dotenv import load_dotenv
from openai import OpenAI

from app.core.db import get_vector_connection

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
logger = logging.getLogger(__name__)

# FIX (weak point #8): now that app/core/ingest_pdfs.py stores one embedding
# per CHUNK instead of one per whole document, retrieving TOP_K chunks is a
# meaningful semantic-search step again -- previously LIMIT 12 against an
# 11-*document* corpus meant "return almost the entire corpus regardless of
# relevance." With chunk-level rows, TOP_K now actually filters down to the
# most relevant passages, and this scales sensibly as the document corpus
# grows (unlike the old whole-document-per-row design).
TOP_K = 8
MAX_CHARS = 22000  # Safety limit for context window


def empower_search(query: str):
    """
    EmpowerNet RAG Search: Retrieves 2026 Labor Laws for wages,
    safety standards, and worker rights.
    """
    try:
        # Generate embedding for the query
        resp = client.embeddings.create(
            input=query,
            model="text-embedding-3-small"
        )
        query_vector = resp.data[0].embedding

        # Database connection (pooled, pgvector-aware)
        conn = get_vector_connection()
        cur = conn.cursor()

        # Semantic Search in pgvector -- now over chunk-level rows
        cur.execute("""
            SELECT content, metadata
            FROM legal_documents
            ORDER BY embedding <=> %s::vector
            LIMIT %s
        """, (query_vector, TOP_K))

        results = cur.fetchall()
        cur.close()
        conn.close()

        if not results:
            return "I couldn't find any specific legal rules for that request."

        # --- TOKEN SAFETY VALVE ---
        context_parts = []
        total_chars = 0

        for content, metadata in results:
            if total_chars + len(content) > MAX_CHARS:
                break
            source = (metadata or {}).get("source", "unknown source")
            context_parts.append(f"[Source: {source}]\n{content}")
            total_chars += len(content)

        context = "\n---\n".join(context_parts)

        # 2. THE MULTI-RIGHTS AUDIT PROMPT
        chat_resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are the EmpowerNet Legal Expert specializing in West Bengal Labor Laws (2026). "
                        "Your goal is to audit a worker's situation against the provided law context.\n\n"
                        "Check for the following markers:\n"
                        "1. WAGES: Is the pay below the minimum wage for their skill/zone?\n"
                        "2. OVERTIME: Are they working >48hrs/week or >9hrs/day without double pay?\n"
                        "3. SAFETY: Does the job lack safety gear, night-shift transport, or CCTV?\n"
                        "4. MATERNITY: Are they being denied the 26-week leave or nursing breaks?\n"
                        "5. DISCRIMINATION: Is there a gender pay gap for similar work?\n\n"
                        "Cite the [Source: ...] filename for any specific figure or clause you rely on. "
                        "If the provided context doesn't cover a marker, say so rather than guessing. "
                        "Provide a clear audit report identifying any violations."
                    )
                },
                {"role": "user", "content": f"Context:\n{context}\n\nWorker's Question/Situation: {query}"}
            ]
        )

        return chat_resp.choices[0].message.content

    except Exception as e:
        logger.error(f"❌ EmpowerNet Search Error: {e}")
        return f"Error accessing legal database: {str(e)}"

if __name__ == "__main__":
    q = input("Ask EmpowerNet a legal or safety question: ")
    print("\n⚖️ EmpowerNet Audit Result:\n", empower_search(q))
