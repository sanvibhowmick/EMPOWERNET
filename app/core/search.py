import os
import json
import psycopg2
from dotenv import load_dotenv
from pgvector.psycopg2 import register_vector
from openai import OpenAI

# 1. Setup
load_dotenv()
DB_URL = os.getenv("DATABASE_URL")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def vesta_search(query):
    resp = client.embeddings.create(
        input=query,
        model="text-embedding-3-small"
    )
    query_vector = resp.data[0].embedding

    conn = psycopg2.connect(DB_URL)
    register_vector(conn)
    cur = conn.cursor()

    # We keep LIMIT 10 but will manage the size in Python
    cur.execute("""
        SELECT content, metadata 
        FROM legal_documents 
        ORDER BY embedding <=> %s::vector 
        LIMIT 10
    """, (query_vector,))
    
    results = cur.fetchall()
    
    if not results:
        return "I couldn't find any relevant rules."

    # --- TOKEN SAFETY VALVE ---
    # We join chunks but stop if we get too close to the 30k limit
    context_parts = []
    total_chars = 0
    # 20,000 chars is roughly 5,000 tokens (very safe for your 30k limit)
    MAX_CHARS = 20000 

    for res in results:
        text = res[0]
        if total_chars + len(text) > MAX_CHARS:
            break
        context_parts.append(text)
        total_chars += len(text)
    
    context = "\n---\n".join(context_parts)
    # --------------------------

    chat_resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system", 
                "content": "You are a legal expert. Find the wage for the specific job requested using the provided context."
            },
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"}
        ]
    )
    
    cur.close()
    conn.close()
    return chat_resp.choices[0].message.content

if __name__ == "__main__":
    q = input("Ask VESTA a legal question: ")
    print("\n🤖 VESTA Answer:\n", vesta_search(q))