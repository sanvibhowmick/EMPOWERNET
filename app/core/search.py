import os
import logging
from dotenv import load_dotenv
import psycopg2
from pgvector.psycopg2 import register_vector
from openai import OpenAI

# 1. Setup
load_dotenv()
DB_URL = os.getenv("DATABASE_URL")
if DB_URL and DB_URL.startswith("postgres://"):
    DB_URL = DB_URL.replace("postgres://", "postgresql://", 1)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
logger = logging.getLogger(__name__)

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

        # Database connection
        conn = psycopg2.connect(DB_URL)
        register_vector(conn)
        cur = conn.cursor()

        # Semantic Search in pgvector
        cur.execute("""
            SELECT content, metadata 
            FROM legal_documents 
            ORDER BY embedding <=> %s::vector 
            LIMIT 12
        """, (query_vector,))
        
        results = cur.fetchall()
        
        if not results:
            return "I couldn't find any specific legal rules for that request."

        # --- TOKEN SAFETY VALVE ---
        context_parts = []
        total_chars = 0
        MAX_CHARS = 22000 # Safety limit for context window

        for res in results:
            text = res[0]
            if total_chars + len(text) > MAX_CHARS:
                break
            context_parts.append(text)
            total_chars += len(text)
        
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
                        "Provide a clear audit report identifying any violations."
                    )
                },
                {"role": "user", "content": f"Context:\n{context}\n\nWorker's Question/Situation: {query}"}
            ]
        )
        
        cur.close()
        conn.close()
        return chat_resp.choices[0].message.content

    except Exception as e:
        logger.error(f"❌ EmpowerNet Search Error: {e}")
        return f"Error accessing legal database: {str(e)}"

if __name__ == "__main__":
    q = input("Ask EmpowerNet a legal or safety question: ")
    print("\n⚖️ EmpowerNet Audit Result:\n", empower_search(q))